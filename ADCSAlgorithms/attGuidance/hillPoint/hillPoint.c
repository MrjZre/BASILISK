/*
    Inertial 3D Spin Module
 
 * University of Colorado, Autonomous Vehicle Systems (AVS) Lab
 * Unpublished Copyright (c) 2012-2015 University of Colorado, All Rights Reserved

 */

/* modify the path to reflect the new module names */
#include "attGuidance/hillPoint/hillPoint.h"
#include <string.h>
#include "ADCSUtilities/ADCSDefinitions.h"
#include "ADCSUtilities/ADCSAlgorithmMacros.h"

/* update this include to reflect the required module input messages */
#include "attDetermination/_GeneralModuleFiles/navStateOut.h"



/*
 Pull in support files from other modules.  Be sure to use the absolute path relative to Basilisk directory.
 */
#include "SimCode/utilities/linearAlgebra.h"
#include "SimCode/utilities/rigidBodyKinematics.h"


/*! This method initializes the ConfigData for this module.
 It checks to ensure that the inputs are sane and then creates the
 output message
 @return void
 @param ConfigData The configuration data associated with this module
 */
void SelfInit_hillPoint(hillPointConfig *ConfigData, uint64_t moduleID)
{
    
    /*! Begin method steps */
    /*! - Create output message for module */
    ConfigData->outputMsgID = CreateNewMessage(ConfigData->outputDataName,
                                               sizeof(attGuidOut),
                                               "attGuidOut",
                                               moduleID);
    v3SetZero(ConfigData->attGuidOut.domega_RN_B);      /* the inertial spin rate is assumed to be constant */

    ConfigData->sigma_BcB = ConfigData->sigma_R0R;      /* these two relative orientations labels are the same */

}

/*! This method performs the second stage of initialization for this module.
 It's primary function is to link the input messages that were created elsewhere.
 @return void
 @param ConfigData The configuration data associated with this module
 */
void CrossInit_hillPoint(hillPointConfig *ConfigData, uint64_t moduleID)
{
    /*! - Get the control data message ID*/
    ConfigData->inputNavID = subscribeToMessage(ConfigData->inputNavName,
                                                sizeof(NavStateOut),
                                                moduleID);

}

/*! This method performs a complete reset of the module.  Local module variables that retain
 time varying states between function calls are reset to their default values.
 @return void
 @param ConfigData The configuration data associated with the MRP steering control
 */
void Reset_hillPoint(hillPointConfig *ConfigData)
{
    double sigma_RR0[3];            /*!< MRP from the original reference frame R0 to the corrected reference frame R */

    /* compute the initial reference frame orientation that takes the corrected body frame into account */
    v3Scale(-1.0, ConfigData->sigma_R0R, sigma_RR0);
    addMRP(ConfigData->sigma_R0N, sigma_RR0, ConfigData->sigma_RN);

    ConfigData->priorTime = 0;              /* reset the prior time flag state.  If set
                                             to zero, the control time step is not evaluated on the
                                             first function call */

}

/*! Add a description of what this main Update() routine does for this module
 @return void
 @param ConfigData The configuration data associated with the MRP Steering attitude control
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Update_hillPoint(hillPointConfig *ConfigData, uint64_t callTime, uint64_t moduleID)
{
    uint64_t            clockTime;
    uint32_t            readSize;
    NavStateOut         nav;                /*!< navigation message */
    double              dt;                 /*!< [s] module update period */


    /*! Begin method steps*/
    /*! - Read the input messages */
    ReadMessage(ConfigData->inputNavID, &clockTime, &readSize,
                sizeof(NavStateOut), (void*) &(nav));



    /* compute control update time */
    if (ConfigData->priorTime != 0) {       /* don't compute dt if this is the first call after a reset */
        dt = (callTime - ConfigData->priorTime)*NANO2SEC;
        if (dt > 10.0) dt = 10.0;           /* cap the maximum control time step possible */
        if (dt < 0.0) dt = 0.0;             /* ensure no negative numbers are used */
    } else {
        dt = 0.;                            /* set dt to zero to not use integration on first function call */
    }
    ConfigData->priorTime = callTime;


    /*
     compute and store output message 
     */
    computeInertialSpinAttitudeError(nav.sigma_BN,
                                     nav.omega_BN_B,
                                     ConfigData,
                                     BOOL_TRUE,         /* integrate and update */
                                     dt,
                                     ConfigData->attGuidOut.sigma_BR,
                                     ConfigData->attGuidOut.omega_BR_B,
                                     ConfigData->attGuidOut.omega_RN_B,
                                     ConfigData->attGuidOut.domega_RN_B);



    WriteMessage(ConfigData->outputMsgID, callTime, sizeof(attGuidOut),   /* update module name */
                 (void*) &(ConfigData->attGuidOut), moduleID);

    return;
}


/*
 * Function: computeInertialSpinAttitudeError
 * Purpose: compute the attitude and rate errors for the Inertial 3D spin control mode.  This function is
 designed to work both here in FSW to compute estimated pointing errors, as well as in the
 simulation code to compute true pointing errors
 * Inputs:
 *   sigma = MRP attitude of body relative to inertial
 *   omega = body rate vector
     ConfigData = module configuration data
 *   integrateFlag = flag to reset the reference orientation
 *                   0 - integrate & evaluate
 *                  -1 - evalute but not integrate)
 *   dt = integration time step (control update period )
 * Outputs:
 *   sigma_BR = MRP attitude error of body relative to reference
 *   omega_BR_B = angular velocity vector error of body relative to reference
 *   omega_RN_B = reference angluar velocity vector in body frame components
 *   domega_RN_B = reference angular acceleration vector in body frame componets
 */
void computeInertialSpinAttitudeError(double sigma_BN[3],
                                      double omega_BN_B[3],
                                      hillPointConfig *ConfigData,
                                      int    integrateFlag,
                                      double dt,
                                      double sigma_BR[3],
                                      double omega_BR_B[3],
                                      double omega_RN_B[3],
                                      double domega_RN_B[3])
{
    double  BN[3][3];               /*!< DCM from inertial to body frame */
    double  RN[3][3];               /*!< DCM from inertial to reference frame */
    double  B[3][3];                /*!< MRP rate matrix */
    double  v3Temp[3];              /*!< temporary 3x1 matrix */
    double  omega_RN_R[3];          /*!< reference angular velocity vector in Reference frame R components */


    if (integrateFlag == BOOL_TRUE) {
        /* integrate reference attitude motion */
        MRP2C(ConfigData->sigma_RN, RN);
        m33MultV3(RN, ConfigData->omega_RN_N, omega_RN_R);
        BmatMRP(ConfigData->sigma_RN, B);
        m33Scale(0.25*dt, B, B);
        m33MultV3(B, omega_RN_R, v3Temp);
        v3Add(ConfigData->sigma_RN, v3Temp, ConfigData->sigma_RN);
        MRPswitch(ConfigData->sigma_RN, 1.0, ConfigData->sigma_RN);
    }

    /* compute attitude error */
    subMRP(sigma_BN, ConfigData->sigma_RN, sigma_BR);

    /* compute rate errors */
    MRP2C(sigma_BN, BN);                                        /* [BN] */
    m33MultV3(BN, ConfigData->omega_RN_N, omega_RN_B);          /* compute reference omega in body frame components */
    v3Subtract(omega_BN_B, omega_RN_B, omega_BR_B);             /* delta_omega = omega_B - [BR].omega.r */
    v3SetZero(domega_RN_B);                                     /* the inertial spin is assumed to be constant */
    
}
