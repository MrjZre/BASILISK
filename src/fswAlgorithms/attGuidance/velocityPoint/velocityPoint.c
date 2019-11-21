/*
 ISC License

 Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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
/*

 Velocity Pointing Guidance Module

 */


#include "attGuidance/velocityPoint/velocityPoint.h"
#include <string.h>
#include <math.h>
#include "fswUtilities/fswDefinitions.h"
#include "simFswInterfaceMessages/macroDefinitions.h"

/* Support files.  Be sure to use the absolute path relative to Basilisk directory. */
#include "simulation/utilities/linearAlgebra.h"
#include "simulation/utilities/rigidBodyKinematics.h"
#include "simulation/utilities/orbitalMotion.h"
#include "simulation/utilities/astroConstants.h"


/*! This method creates the module output message of type [AttRefFswMsg](\ref AttRefFswMsg).
 @return void
 @param configData The configuration data associated with RW null space model
 @param moduleID The ID associated with the configData
 */
void SelfInit_velocityPoint(velocityPointConfig *configData, int64_t moduleID)
{
    configData->bskPrint = _BSKPrint();
    /*! - Create output message for module */
    configData->outputMsgID = CreateNewMessage(configData->outputDataName,
                                               sizeof(AttRefFswMsg),
                                               "AttRefFswMsg",
                                               moduleID);
}

/*! This method performs the second stage of initialization
 interface.  This module has two messages to subscribe to of type [EphemerisIntMsg](\ref EphemerisIntMsg) and [NavTransIntMsg](\ref NavTransIntMsg).
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The ID associated with the configData
 */
void CrossInit_velocityPoint(velocityPointConfig *configData, int64_t moduleID)
{
    /*! - inputCelID provides the planet ephemeris message.  Note that if this message does
     not exist, this subscribe function will create an empty planet message.  This behavior
     is by design such that if a planet doesn't have a message, default (0,0,0) position
     and velocity vectors are assumed. */
    configData->inputCelID = subscribeToMessage(configData->inputCelMessName,
                                                sizeof(EphemerisIntMsg), moduleID);
    /*! - inputNavID provides the current spacecraft location and velocity */
    configData->inputNavID = subscribeToMessage(configData->inputNavDataName,
                                                sizeof(NavTransIntMsg), moduleID);
}

/*! This method performs the module reset capability.  This module has no actions.
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The ID associated with the configData
 */
void Reset_velocityPoint(velocityPointConfig *configData, uint64_t callTime, int64_t moduleID)
{

}

/*! This method creates a orbit velocity frame reference message.  The desired orientation is
 defined within the module.
 @return void
 @param configData The configuration data associated with the null space control
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The ID associated with the configData
 */
void Update_velocityPoint(velocityPointConfig *configData, uint64_t callTime, int64_t moduleID)
{
    /*! - Read input message */
    uint64_t            timeOfMsgWritten;
    uint32_t            sizeOfMsgWritten;
    NavTransIntMsg      navData;
    EphemerisIntMsg     primPlanet;
    AttRefFswMsg        attRefOut;

    /*! - zero the output message */
    memset(&attRefOut, 0x0, sizeof(AttRefFswMsg));

    /*! - zero and read the input messages */
    memset(&primPlanet, 0x0, sizeof(EphemerisIntMsg));
    ReadMessage(configData->inputCelID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(EphemerisIntMsg), &primPlanet, moduleID);
    memset(&navData, 0x0, sizeof(NavTransIntMsg));
    ReadMessage(configData->inputNavID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(NavTransIntMsg), &navData, moduleID);


    /*! - Compute and store output message */
    computeVelocityPointingReference(configData,
                                     navData.r_BN_N,
                                     navData.v_BN_N,
                                     primPlanet.r_BdyZero_N,
                                     primPlanet.v_BdyZero_N,
                                     &attRefOut);

    WriteMessage(configData->outputMsgID, callTime, sizeof(AttRefFswMsg),   /* update module name */
                 (void*) &(attRefOut), moduleID);

    return;
}


void computeVelocityPointingReference(velocityPointConfig *configData,
                                      double r_BN_N[3],
                                      double v_BN_N[3],
                                      double celBdyPositonVector[3],
                                      double celBdyVelocityVector[3],
                                      AttRefFswMsg *attRefOut)
{
    double  dcm_RN[3][3];            /* DCM from inertial to reference frame */

    double  r[3];                    /* relative position vector of the spacecraft with respect to the orbited planet */
    double  v[3];                    /* relative velocity vector of the spacecraft with respect to the orbited planet  */
    double  h[3];                    /* orbit angular momentum vector */
    double  rm;                      /* orbit radius */
    double  hm;                      /* module of the orbit angular momentum vector */

    double  dfdt;                    /* rotational rate of the orbit frame */
    double  ddfdt2;                  /* rotational acceleration of the frame */
    double  omega_RN_R[3];           /* reference angular velocity vector in Reference frame R components */
    double  domega_RN_R[3];          /* reference angular acceleration vector in Reference frame R components */
    classicElements oe;              /* Orbit Elements set */

    double  temp33[3][3];
    double  temp;
    double  denom;

    /* zero the reference rate and acceleration vectors */
    v3SetZero(omega_RN_R);
    v3SetZero(domega_RN_R);

    /* Compute relative position and velocity of the spacecraft with respect to the main celestial body */
    v3Subtract(r_BN_N, celBdyPositonVector, r);
    v3Subtract(v_BN_N, celBdyVelocityVector, v);

    /* Compute RN */
    v3Normalize(v, dcm_RN[1]);
    v3Cross(r, v, h);
    v3Normalize(h, dcm_RN[2]);
    v3Cross(dcm_RN[1], dcm_RN[2], dcm_RN[0]);

    /* Compute R-frame orientation */
    C2MRP(dcm_RN, attRefOut->sigma_RN);

    /* Compute R-frame inertial rate and acceleration */
    rm = v3Norm(r);
    hm = v3Norm(h);
    /* Robustness check */
    if(rm > 1.) {
        rv2elem(configData->mu, r, v, &oe);
        dfdt = hm / (rm * rm);  /* true anomaly rate */
        ddfdt2    = - 2.0 * (v3Dot(v, r) / (rm * rm)) * dfdt;
        denom = 1 + oe.e * oe.e + 2 * oe.e * cos(oe.f);
        temp = (1 + oe.e * cos(oe.f)) / denom;
        omega_RN_R[2]  = dfdt * temp;
        domega_RN_R[2] = ddfdt2 * temp - dfdt*dfdt* oe.e *(oe.e*oe.e - 1)*sin(oe.f) / (denom*denom);
    } else {
        dfdt   = 0.;
        ddfdt2 = 0.;
    }
    m33Transpose(dcm_RN, temp33);
    m33MultV3(temp33, omega_RN_R, attRefOut->omega_RN_N);
    m33MultV3(temp33, domega_RN_R, attRefOut->domega_RN_N);
}
