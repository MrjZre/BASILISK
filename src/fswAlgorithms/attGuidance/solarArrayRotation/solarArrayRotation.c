/*
 ISC License

 Copyright (c) 2022, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

 Permission to use, copy, modify, and/or distribute this software for any
 purpose with or without fee is hereby granted, provided that the above
 copyright notice and this permission notice appear in all copies.

 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */


/* modify the path to reflect the new module names */
#include "solarArrayRotation.h"
#include "string.h"
#include <math.h>

/* Support files.  Be sure to use the absolute path relative to Basilisk directory. */
#include "architecture/utilities/linearAlgebra.h"
#include "architecture/utilities/rigidBodyKinematics.h"


/*!
    This method initializes the output messages for this module.
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The module identifier
 */
void SelfInit_solarArrayRotation(solarArrayRotationConfig *configData, int64_t moduleID)
{
    SpinningBodyRefMsg_C_init(&configData->spinningBodyRefOutMsg);
}


/*! This method performs a complete reset of the module.  Local module variables that retain
 time varying states between function calls are reset to their default values.
 @return void
 @param configData The configuration data associated with the module
 @param callTime [ns] time the method is called
 @param moduleID The module identifier
*/
void Reset_solarArrayRotation(solarArrayRotationConfig *configData, uint64_t callTime, int64_t moduleID)
{
    // check if the required input message is included
    if (!NavAttMsg_C_isLinked(&configData->attNavInMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: solarArrayAngle.attNavInMsg wasn't connected.");
    }
    // check if the required input message is included
    if (!AttRefMsg_C_isLinked(&configData->attRefInMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: solarArrayAngle.attRefInMsg wasn't connected.");
    }
    // check if the required input message is included
    if (!SpinningBodyMsg_C_isLinked(&configData->spinningBodyInMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: solarArrayAngle.spinningBodyInMsg wasn't connected.");
    }
}

/*! Add a description of what this main Update() routine does for this module
 @return void
 @param configData The configuration data associated with the module
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The module identifier
*/
void Update_solarArrayRotation(solarArrayRotationConfig *configData, uint64_t callTime, int64_t moduleID)
{
    /*! - Create buffer messages */
    NavAttMsgPayload            attNavIn;
    AttRefMsgPayload            attRefIn;
    SpinningBodyMsgPayload      spinningBodyIn;
    SpinningBodyRefMsgPayload   spinningBodyRefOut;

    /*! - zero the output message */
    spinningBodyRefOut = SpinningBodyRefMsg_C_zeroMsgPayload();

    /*! read the attitude navigation message */
    attNavIn = NavAttMsg_C_read(&configData->attNavInMsg);

    /*! read the attitude reference message */
    attRefIn = AttRefMsg_C_read(&configData->attRefInMsg);

    /*! read the solar array angle message */
    spinningBodyIn = SpinningBodyMsg_C_read(&configData->spinningBodyInMsg);

    /* read Sun direction in B frame from the attNav message */
    double rS_B[3];
    v3Normalize(attNavIn.vehSunPntBdy, rS_B);

    /* normalize a1_B and a2_B from module input */
    double a1_B[3], a2_B_nominal[3], a2_B_target[3];
    v3Normalize(configData->a1_B, a1_B);
    v3Normalize(configData->a2_B, a2_B_nominal);

    /* compute a2_B target */
    double dotP = v3Dot(a1_B, rS_B);
    for (int n = 0; n < 3; n++) {
        a2_B_target[n] = rS_B[n] - dotP * a1_B[n];
    }
    v3Normalize(a2_B_target, a2_B_nominal);

    /* compute rotation angle theta */
    double thetaR;
    double thetaC, sinThetaC, cosThetaC;
    // clip thetaC between 0 an pi
    sinThetaC = sin(spinningBodyIn.theta);
    cosThetaC = cos(spinningBodyIn.theta);
    thetaC = atan2(sinThetaC, cosThetaC);
    // compute shortest angle difference
    if (v3Norm(a2_B_target) < EPS) {
        thetaR = thetaC;
    }
    else {
        thetaR = acos( fmin(fmax(v3Dot(a2_B_nominal, a2_B_target),-1),1) );
        if (thetaR - thetaC > M_PI/2) {
            thetaC += M_PI;
        }
        else if (thetaR - thetaC < - M_PI/2) {
            thetaC -= M_PI;
        }
    }

    spinningBodyRefOut.thetaR = thetaR;
    spinningBodyRefOut.thetaDotR = 0;
    spinningBodyRefOut.thetaC = thetaC;
    spinningBodyRefOut.thetaDotC = spinningBodyIn.thetaDot;

    /* write output message */
    SpinningBodyRefMsg_C_write(&spinningBodyRefOut, &configData->spinningBodyRefOutMsg, moduleID, callTime);

    return;
}