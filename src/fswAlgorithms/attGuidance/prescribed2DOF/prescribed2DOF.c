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

/* Modify the path to reflect the new module names */
#include "prescribed2DOF.h"
#include "string.h"
#include <math.h>
#include <stdlib.h>
#include <stdbool.h>
#include "architecture/utilities/linearAlgebra.h"
#include "architecture/utilities/rigidBodyKinematics.h"

/*! This method initializes the output messages for this module.
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The module identifier
 */
void SelfInit_prescribed2DOF(Prescribed2DOFConfig *configData, int64_t moduleID)
{
    PrescribedMotionMsg_C_init(&configData->prescribedMotionOutMsg);

    /*! Initialize variables set by the user to flagged values to ensure they are properly set by the user */
    // *** *** *** NOTE: SelfInit() is called after InitializeSimulation(), The following lines will overwrite the user-configured parameters *** *** ***
    //configData->phiDDotMax = 0;
    //v3SetZero(configData->rotAxis1_M);
    //v3SetZero(configData->rotAxis2_F1);
}

/*! This method performs a complete reset of the module.  Local module variables that retain
 time varying states between function calls are reset to their default values.
 @return void
 @param configData The configuration data associated with the module
 @param callTime [ns] time the method is called
 @param moduleID The module identifier
*/
void Reset_prescribed2DOF(Prescribed2DOFConfig *configData, uint64_t callTime, int64_t moduleID)
{
    /*! Check if the required input messages are included */
    if (!SpinningBodyMsg_C_isLinked(&configData->spinningBodyRef1InMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.spinningBodyRef1InMsg wasn't connected.");
    }
    if (!SpinningBodyMsg_C_isLinked(&configData->spinningBodyRef2InMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.spinningBodyRef2InMsg wasn't connected.");
    }

    if (!PrescribedMotionMsg_C_isLinked(&configData->prescribedMotionInMsg)) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.prescribedMotionInMsg wasn't connected.");
    }

    if (configData->phiDDotMax < 0) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.phiDDotMax wasn't set.");
    }

    if (v3Norm(configData->rotAxis1_M) < 1e-6) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.rotAxis1_M wasn't set.");
    }

    if (v3Norm(configData->rotAxis2_F1) < 1e-6) {
        _bskLog(configData->bskLogger, BSK_ERROR, "Error: prescribed2DOF.rotAxis2_F1 wasn't set.");
    }

    /*! Store initial time */
    configData->tInit = callTime*1e-9;

    /*! Set initial convergence to true */
    configData->convergence = true;

    /* Set the reference and accumulated phi to zero */
    configData->phiRef = 0.0;
    configData->phiRefAccum = 0.0;
    configData->phiAccum = 0.0;
}

/*! Add a description of what this main Update() routine does for this module
 @return void
 @param configData The configuration data associated with the module
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The module identifier
*/
void Update_prescribed2DOF(Prescribed2DOFConfig *configData, uint64_t callTime, int64_t moduleID)
{
    /*! Create buffer messages */
    SpinningBodyMsgPayload spinningBodyRef1In;
    SpinningBodyMsgPayload spinningBodyRef2In;
    SpinningBodyMsgPayload spinningBodyOut;
    PrescribedMotionMsgPayload prescribedMotionIn;
    PrescribedMotionMsgPayload prescribedMotionOut;

    /*! Zero the output message */
    spinningBodyOut = SpinningBodyMsg_C_zeroMsgPayload();
    prescribedMotionOut = PrescribedMotionMsg_C_zeroMsgPayload();

    /*! Read the input messages */
    spinningBodyRef1In = SpinningBodyMsg_C_zeroMsgPayload();
    if (SpinningBodyMsg_C_isWritten(&configData->spinningBodyRef1InMsg))
    {
        spinningBodyRef1In = SpinningBodyMsg_C_read(&configData->spinningBodyRef1InMsg);
    }
    spinningBodyRef2In = SpinningBodyMsg_C_zeroMsgPayload();
    if (SpinningBodyMsg_C_isWritten(&configData->spinningBodyRef2InMsg))
    {
        spinningBodyRef2In = SpinningBodyMsg_C_read(&configData->spinningBodyRef2InMsg);
    }
    prescribedMotionIn = PrescribedMotionMsg_C_zeroMsgPayload();
    if (PrescribedMotionMsg_C_isWritten(&configData->prescribedMotionInMsg))
    {
        prescribedMotionIn = PrescribedMotionMsg_C_read(&configData->prescribedMotionInMsg);
    }

    /*! Copy the input variables to the module variables */
    v3Copy(prescribedMotionIn.r_FM_M, configData->r_FM_M);
    v3Copy(prescribedMotionIn.rPrime_FM_M, configData->rPrime_FM_M);
    v3Copy(prescribedMotionIn.rPrimePrime_FM_M, configData->rPrimePrime_FM_M);
    v3Copy(prescribedMotionIn.omega_FM_F, configData->omega_FM_F);
    v3Copy(prescribedMotionIn.omegaPrime_FM_F, configData->omegaPrime_FM_F);
    v3Copy(prescribedMotionIn.sigma_FM, configData->sigma_FM);

    /*! If an attitude maneuver is required this loop is entered and the module parameters are updated */
    if ((SpinningBodyMsg_C_timeWritten(&configData->spinningBodyRef1InMsg) <= callTime || SpinningBodyMsg_C_timeWritten(&configData->spinningBodyRef2InMsg) <= callTime ) && configData->convergence)
    {
        /*! Define the initial time */
        configData->tInit = callTime*1e-9;

        /*! Calculate the current attitude DCM with respect to the mount M frame */
        double dcm_FM[3][3];
        MRP2C(configData->sigma_FM, dcm_FM);
        m33Copy(dcm_FM, configData->dcm_F0M);

        /*! Grab reference variables from the spinningBody input messages */
        double theta1Ref = spinningBodyRef1In.theta; // [rad]
        double theta2Ref = spinningBodyRef2In.theta; // [rad]
        double thetaDot1Ref = spinningBodyRef1In.thetaDot; // [rad/s]
        double thetaDot2Ref = spinningBodyRef2In.thetaDot; // [rad/s]

        /*! Convert both reference angles and rotation axes to PRVs */
        double prv_F1M_array[3];
        double prv_F2F1_array[3];
        v3Normalize(configData->rotAxis1_M, configData->rotAxis1_M);
        v3Normalize(configData->rotAxis2_F1, configData->rotAxis2_F1);
        v3Scale(theta1Ref, configData->rotAxis1_M, prv_F1M_array);
        v3Scale(theta2Ref, configData->rotAxis2_F1, prv_F2F1_array);

        /*! Convert the reference PRVs to DCMs */
        double dcm_F1M[3][3];
        double dcm_F2F1[3][3];
        PRV2C(prv_F1M_array, dcm_F1M);
        PRV2C(prv_F2F1_array, dcm_F2F1);

        /*! Combine the two computed reference DCMs to a single reference DCM */
        double dcm_F2M[3][3];
        m33MultM33(dcm_F2F1, dcm_F1M, dcm_F2M);

        /*! Compute the PRV from the current attitude to the reference attitude, dcm_F2F */
        double dcm_F2F[3][3];
        m33MultM33t(dcm_F2M, dcm_FM, dcm_F2F);
        double prv_F2F_array[3];
        C2PRV(dcm_F2F, prv_F2F_array);

        /*! Compute the single PRV reference angle for the attitude maneuver */
        v3Normalize(prv_F2F_array, configData->rotAxis_M);
        configData->phiRefAccum = configData->phiAccum;
        configData->phiRef = v3Dot(prv_F2F_array, configData->rotAxis_M);

        /*! Define temporal information */
        double convTime = sqrt(fabs(configData->phiRef) * 4 / configData->phiDDotMax); // [s] Time for individual attitude maneuvers
        configData->tf = configData->tInit + convTime;
        configData->ts = convTime / 2 + configData->tInit;

        // Define constants for analytic parabolas
        configData->a = 0.5 * configData->phiRef / ((configData->ts - configData->tInit) * (configData->ts - configData->tInit));
        configData->b = -0.5 * configData->phiRef / ((configData->ts - configData->tf) * (configData->ts - configData->tf));

        /*! Set convergence to false until the attitude maneuver is complete */
        configData->convergence = false;
    }

    /*! Store the current simulation time */
    double t = callTime*1e-9; // [s]

    /*! Define scalar module states */
    double phiDDot;
    double phiDot;

    /*! Compute the scalar states analytically: phi, phiDot, and phiDDot */
    if ((t < configData->ts || t == configData->ts) && configData->tf != configData->tInit) // This section is entered during the first half of the attitude maneuver
    {
        phiDDot = configData->phiDDotMax;
        phiDot = phiDDot * (t - configData->tInit);
        configData->phi = configData->a * (t - configData->tInit) * (t - configData->tInit);
    }
    else if ( t > configData->ts && t <= configData->tf && configData->tf != configData->tInit) // This section is entered during the first half of the attitude maneuver
    {
        phiDDot = -1 * configData->phiDDotMax;
        phiDot = phiDDot * (t - configData->tf );
        configData->phi = configData->b * (t - configData->tf) * (t - configData->tf) + configData->phiRef;
    }
    else // This section is entered if the current PRV angle has converged to the reference PRV angle
    {
        phiDDot = 0.0;
        phiDot = 0.0;
        configData->phi = configData->phiRef;
        configData->convergence = true;
    }

    /*! Log the accumulated PRV angle for plotting */
    configData->phiAccum = configData->phiRefAccum + configData->phi;

    /*! Determine the omega_FM_F and omegaPrime_FM_F prescribed parameters */
    v3Normalize(configData->rotAxis_M, configData->rotAxis_M);
    v3Scale(phiDot, configData->rotAxis_M, configData->omega_FM_F);
    v3Scale(phiDDot, configData->rotAxis_M, configData->omegaPrime_FM_F);

    /*! Determine the current attitude with respect to the mount M frame, sigma_FM */
    /*! Calculate current PRV with respect to the initial attitude F0 frame */
    double dcm_FF0[3][3];
    double prv_FF0_array[3];
    v3Scale(configData->phi, configData->rotAxis_M, prv_FF0_array);
    PRV2C(prv_FF0_array, dcm_FF0);

    /*! Determine the dcm_FM for the current attitude with respect to the mount M frame */
    double dcm_FM[3][3];
    m33MultM33(dcm_FF0, configData->dcm_F0M, dcm_FM);
    C2MRP(dcm_FM, configData->sigma_FM);

    /*! Copy the module prescribed variables to the prescribed output message */
    v3Copy(configData->r_FM_M, prescribedMotionOut.r_FM_M);
    v3Copy(configData->rPrime_FM_M, prescribedMotionOut.rPrime_FM_M);
    v3Copy(configData->rPrimePrime_FM_M, prescribedMotionOut.rPrimePrime_FM_M);
    v3Copy(configData->omega_FM_F, prescribedMotionOut.omega_FM_F);
    v3Copy(configData->omegaPrime_FM_F, prescribedMotionOut.omegaPrime_FM_F);
    v3Copy(configData->sigma_FM, prescribedMotionOut.sigma_FM);

    /*! Write the output message */
    PrescribedMotionMsg_C_write(&prescribedMotionOut, &configData->prescribedMotionOutMsg, moduleID, callTime);

    return;
}
