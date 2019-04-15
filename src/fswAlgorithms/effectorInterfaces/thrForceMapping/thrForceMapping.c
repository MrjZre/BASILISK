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
    Simple Thruster Force Evaluation from

 */

/* modify the path to reflect the new module names */
#include "effectorInterfaces/thrForceMapping/thrForceMapping.h"

/* update this include to reflect the required module input messages */
#include "simFswInterfaceMessages/macroDefinitions.h"
#include <string.h>
#include <math.h>


/*
 Pull in support files from other modules.  Be sure to use the absolute path relative to Basilisk directory.
 */
#include "simulation/utilities/linearAlgebra.h"
#include "simulation/utilities/bsk_Print.h"


/*! This method initializes the ConfigData for this module.
 It checks to ensure that the inputs are sane and then creates the
 output message
 @return void
 @param ConfigData The configuration data associated with this module
 */
void SelfInit_thrForceMapping(thrForceMappingConfig *ConfigData, uint64_t moduleID)
{
    /*! Begin method steps */
    /*! - Create output message for module */
    ConfigData->outputMsgID = CreateNewMessage(ConfigData->outputDataName,
                                               sizeof(THRArrayCmdForceFswMsg),
                                               "THRArrayCmdForceFswMsg",
                                               moduleID);
}

/*! This method performs the second stage of initialization for this module.
 It's primary function is to link the input messages that were created elsewhere.
 @return void
 @param ConfigData The configuration data associated with this module
 */
void CrossInit_thrForceMapping(thrForceMappingConfig *ConfigData, uint64_t moduleID)
{
    /*! - Get the input message ID's */
    ConfigData->inputVehControlID = subscribeToMessage(ConfigData->inputVehControlName,
                                                sizeof(CmdTorqueBodyIntMsg),
                                                moduleID);

    ConfigData->inputThrusterConfID = subscribeToMessage(ConfigData->inputThrusterConfName,
                                                       sizeof(THRArrayConfigFswMsg),
                                                       moduleID);

    ConfigData->inputVehicleConfigDataID = subscribeToMessage(ConfigData->inputVehicleConfigDataName,
                                                              sizeof(VehicleConfigFswMsg), moduleID);

}

/*! This method performs a complete reset of the module.  Local module variables that retain
 time varying states between function calls are reset to their default values.
 @return void
 @param ConfigData The configuration data associated with the module
 */
void Reset_thrForceMapping(thrForceMappingConfig *ConfigData, uint64_t callTime, uint64_t moduleID)
{
    double             *pAxis;                 /*!< pointer to the current control axis */
    int                 i;
    THRArrayConfigFswMsg   localThrusterData;     /*!< local copy of the thruster data message */
    uint64_t            timeOfMsgWritten;
    uint32_t            sizeOfMsgWritten;

    /* configure the number of axes that are controlled */
    ConfigData->numOfAxesToBeControlled = 0;
    for (i=0;i<3;i++)
    {
        pAxis = ConfigData->controlAxes_B + 3*ConfigData->numOfAxesToBeControlled;
        if (v3Norm(pAxis) > 0.1) {
            v3Normalize(pAxis,pAxis);
            ConfigData->numOfAxesToBeControlled += 1;
        } else {
            break;
        }
    }
    if (ConfigData->numOfAxesToBeControlled==0) {
        BSK_PRINT(MSG_WARNING,"thrForceMapping() is not setup to control any axes!\n");
    }
    if (ConfigData->thrForceSign ==0) {
        BSK_PRINT(MSG_WARNING,"thrForceMapping() must have posThrustFlag set to either +1 or -1\n");
    }


    /* read in the support messages */
    ReadMessage(ConfigData->inputThrusterConfID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(THRArrayConfigFswMsg), &localThrusterData, moduleID);
    ReadMessage(ConfigData->inputVehicleConfigDataID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(VehicleConfigFswMsg), (void*) &(ConfigData->sc), moduleID);

    /* read in the thruster position and thruster force heading information */
    /* Note: we will still need to correct for the S to B transformation */
    ConfigData->numThrusters = localThrusterData.numThrusters;
    for(i=0; i<ConfigData->numThrusters; i=i+1)
    {
        v3Copy(localThrusterData.thrusters[i].rThrust_B, ConfigData->rThruster_B[i]);
        v3Copy(localThrusterData.thrusters[i].tHatThrust_B, ConfigData->gtThruster_B[i]);
        ConfigData->thrForcMag[i] = localThrusterData.thrusters[i].maxThrust;
    }
    memset(&(ConfigData->thrusterForceOut), 0x0, sizeof(THRArrayCmdForceFswMsg));

}

/*! Add a description of what this main Update() routine does for this module
 @return void
 @param ConfigData The configuration data associated with the module
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Update_thrForceMapping(thrForceMappingConfig *ConfigData, uint64_t callTime, uint64_t moduleID)
{
    uint64_t    timeOfMsgWritten;
    uint32_t    sizeOfMsgWritten;
    double      F[MAX_EFF_CNT];               /*!< [N]     vector of commanded thruster forces */
    double      Fbar[MAX_EFF_CNT];            /*!< [N]     vector of intermediate thruster forces */
    int         i,c;
    int         counterPosForces;             /*!< []      counter for number of positive thruster forces */
    double      D[MAX_EFF_CNT][3];            /*!< [m]     mapping matrix from thruster forces to body torque */
    double      Dbar[MAX_EFF_CNT][3];         /*!< [m]     reduced mapping matrix
                                                           Note, the vectors are stored as row vectors, not column vectors */
    double      Lr_B[3];                      /*!< [Nm]    commanded ADCS control torque */
    double      Lr_offset[3];
    double      LrLocal[3];
    int         thrusterUsed[MAX_EFF_CNT];    /*!< []      Array of flags indicating if this thruster is used for the Lr_j */
    double      rThrusterRelCOM_B[MAX_EFF_CNT][3];/*!< [m]     local copy of the thruster locations relative to COM */
    uint32_t    numOfAvailableThrusters;      /*!< []      number of available thrusters */
    double      BLr_B[3];                     /*!< [Nm]    Control torque that we actually control*/
    double      maxFractUse;                  /*!< []      ratio of maximum requested thruster force relative to maximum thruster limit */

    /*! Begin method steps*/
    /*! - Read the input messages */
    ReadMessage(ConfigData->inputVehControlID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(CmdTorqueBodyIntMsg), (void*) &(Lr_B), moduleID);
    ReadMessage(ConfigData->inputVehicleConfigDataID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(VehicleConfigFswMsg), (void*) &(ConfigData->sc), moduleID);


    /* compute thruster locations relative to COM */
    for (i=0;i<ConfigData->numThrusters;i++) {
        v3Subtract(ConfigData->rThruster_B[i], ConfigData->sc.CoM_B, rThrusterRelCOM_B[i]);
    }


    /* clear the net thruster force output array */
    memset(F,0x0,MAX_EFF_CNT*sizeof(double));

    /* temporary available thruster assignment until the thruster availability is read in through a message */
    numOfAvailableThrusters = ConfigData->numThrusters;


    /* compute general mapping matrix */
    memset(Lr_offset, 0x0, 3*sizeof(double));
    for(i=0; i<numOfAvailableThrusters; i=i+1)
    {
        v3Cross(rThrusterRelCOM_B[i], ConfigData->gtThruster_B[i], D[i]);
        if(ConfigData->thrForceSign < 0)
        {
            v3Scale(ConfigData->thrForcMag[i], D[i], LrLocal);
            v3Subtract(Lr_offset, LrLocal, Lr_offset);
        }
    }
    v3Add(Lr_offset, Lr_B, Lr_B);
    findMinimumNormForce(ConfigData, D, Lr_B, numOfAvailableThrusters, F, BLr_B);
    if (ConfigData->thrForceSign>0) substractMin(F, numOfAvailableThrusters);

    if (numOfAvailableThrusters != ConfigData->numThrusters || ConfigData->thrForceSign<0) {
        counterPosForces = 0;
        memset(thrusterUsed,0x0,MAX_EFF_CNT*sizeof(int));
        for (i=0;i<numOfAvailableThrusters;i++) {
            if (F[i]*ConfigData->thrForceSign > ConfigData->epsilon) {
                thrusterUsed[i] = 1;
                v3Copy(D[i], Dbar[counterPosForces]);
                counterPosForces += 1;
            }
        }
        findMinimumNormForce(ConfigData, Dbar, Lr_B, counterPosForces, Fbar, BLr_B);

        c = 0;
        for (i=0;i<numOfAvailableThrusters;i++) {
            if (thrusterUsed[i]) {
                F[i] = Fbar[c];
                c += 1;
            } else {
                F[i] = 0.0;
            }
        }
        if (ConfigData->thrForceSign>0) substractMin(F, numOfAvailableThrusters);
    }

    ConfigData->outTorqAngErr = computeTorqueAngErr(D, BLr_B, numOfAvailableThrusters, F,
        ConfigData->thrForcMag);
    maxFractUse = 0.0;
    /*
        check if the angle between the request and actual torque exceeds a limit.  If then, then uniformly scale
        all thruster forces values to not exceed saturation.
        If the angle threshold is negative, then this scaling is bypassed.
     */
    if(ConfigData->outTorqAngErr > ConfigData->angErrThresh)
    {
        for(i=0; i<numOfAvailableThrusters; i++)
        {
            if(ConfigData->thrForcMag[i] > 0.0 && fabs(F[i])/ConfigData->thrForcMag[i] > maxFractUse)
            {
                maxFractUse = fabs(F[i])/ConfigData->thrForcMag[i];
            }
        }
        /* only scale the requested thruster force if one or more thrusters are saturated */
        if(maxFractUse > 1.0)
        {
            vScale(1.0/maxFractUse, F, numOfAvailableThrusters, F);
            ConfigData->outTorqAngErr = computeTorqueAngErr(D, BLr_B, numOfAvailableThrusters, F,
                                                            ConfigData->thrForcMag);
        }
    }

    /*
     store the output message 
     */
    mCopy(F, ConfigData->numThrusters, 1, ConfigData->thrusterForceOut.thrForce);
    WriteMessage(ConfigData->outputMsgID, callTime, sizeof(THRArrayCmdForceFswMsg),   /* update module name */
                 (void*) &(ConfigData->thrusterForceOut), moduleID);

    return;
}


void substractMin(double *F, uint32_t size)
{
    double minValue;                        /*!< [N]    min or max value of the force set */
    int    i;

    minValue = F[0];
    for (i=1;i<size;i++) {
        if (F[i] < minValue) {
            minValue = F[i];
        }
    }
    for (i=0;i<size;i++){
        F[i] -= minValue;
    }

    return;
}

void findMinimumNormForce(thrForceMappingConfig *ConfigData,
                          double D[MAX_EFF_CNT][3], double Lr_B[3], uint32_t numForces, double F[MAX_EFF_CNT], double BLr_b[3])
{

    int i,j,k;                                  /*!< []     counters */
    double      DDT[3][3];                      /*!< [m^2]  [D].[D]^T matrix */
    double      CD[2][MAX_EFF_CNT];             /*!< [m]    [C].[D] */
    double      CDCDT22[2][2];                  /*!< [m^2]  ([C].[D]).([C].[D])^T */
    double      CDCDT11;                        /*!< [m^2]  ([C].[D]).([C].[D])^T */
    double      matInv33[3][3];
    double      matInv22[2][2];
    double      tempVec[3];

    /* zero the output force vector */
    memset(F,0x0,MAX_EFF_CNT*sizeof(double));

    /* find [D].[D]^T */
    for(i=0; i<3; i++) {
        for(j=0; j<3; j++) {
            DDT[i][j] = 0.0;
            for (k=0;k<numForces;k++) {
                DDT[i][j] += D[k][i] * D[k][j];
            }
        }
    }

    v3SetZero(BLr_b);
    v3SetZero(tempVec);
    if (m33Determinant(DDT) > ConfigData->epsilon) {
        /* find minimum norm inverse to control all three axes */
        m33Inverse(DDT, matInv33);
        for (i=0;i<ConfigData->numOfAxesToBeControlled;i++) {
            v3Scale(v3Dot(ConfigData->controlAxes_B+3*i, Lr_B), ConfigData->controlAxes_B+3*i, tempVec);
            v3Add(BLr_b, tempVec, BLr_b);
        }
        m33MultV3(matInv33, BLr_b, tempVec);
        for (i=0;i<numForces;i++) {
            F[i] = 0.0;
            for (k=0;k<3;k++) {
                F[i] += D[i][k]*tempVec[k];
            }
        }
    } else {
        if (ConfigData->numOfAxesToBeControlled == 2) {
            /* compute the minimum norm solution on the 2D [C] subspace */
            for (i=0;i<2;i++){
                v3Scale(v3Dot(ConfigData->controlAxes_B+3*i, Lr_B),
                    ConfigData->controlAxes_B+3*i, tempVec);
                v3Add(BLr_b, tempVec, BLr_b);
                for (j=0;j<numForces;j++) {
                    CD[i][j] = v3Dot(ConfigData->controlAxes_B+3*i, D[j]);
                }
            }
            for (i=0;i<2;i++) {
                for (j=0;j<2;j++) {
                    CDCDT22[i][j] = 0.0;
                    for (k=0;k<numForces;k++) {
                        CDCDT22[i][j] += CD[i][k]*CD[j][k];
                    }
                }
            }

            if (m22Determinant(CDCDT22) > ConfigData->epsilon) {
                tempVec[0] = v3Dot(ConfigData->controlAxes_B,   Lr_B);
                tempVec[1] = v3Dot(ConfigData->controlAxes_B+3, Lr_B);
                m22Inverse(CDCDT22, matInv22);
                m22MultV2(matInv22, tempVec, tempVec);

                for (i=0;i<numForces;i++) {
                    F[i] = 0.;
                    for (k=0;k<2;k++) {
                        F[i] += CD[k][i]*tempVec[k];
                    }
                }
            }
        }

        if (ConfigData->numOfAxesToBeControlled == 1) {
            /* compute the minimum norm solution on the 1D [C] subspace */
            v3Scale(v3Dot(ConfigData->controlAxes_B, Lr_B),
                    ConfigData->controlAxes_B, BLr_b);
            for (j=0;j<numForces;j++) {
                CD[0][j] = v3Dot(ConfigData->controlAxes_B, D[j]);
            }
            CDCDT11 = 0.0;
            for (k=0;k<numForces;k++) {
                CDCDT11 += CD[0][k]*CD[0][k];
            }

            if (CDCDT11 > ConfigData->epsilon && fabs(CDCDT11) > 0.0) {
                tempVec[0] = v3Dot(ConfigData->controlAxes_B,   Lr_B);
                tempVec[0] = tempVec[0] / CDCDT11;
                for (i=0;i<numForces;i++) {
                    F[i] = CD[0][i]*tempVec[0];
                }
            }
        }
    }

    return;
}

double computeTorqueAngErr(double D[MAX_EFF_CNT][3], double BLr_B[3], uint32_t numForces,
                           double F[MAX_EFF_CNT], double FMag[MAX_EFF_CNT])

{
    double returnAngle = 0.0;       /*!< [rad]  angle between requested and actual torque vector */
    double tauActual_B[3];          /*!< [Nm]   control torque with current thruster solution */
    double BLr_hat_B[3];            /*!< []     normalized BLr_B vector */
    double LrEffector_B[3];         /*!< [Nm]   torque of an individual thruster effector */
    double thrusterForce;           /*!< [N]    saturation constrained thruster force */
    int i;

    /* make sure a control torque is requested, otherwise just return a zero angle error */
    if (v3Norm(BLr_B) > 0.0000000001) {
        v3Normalize(BLr_B, BLr_hat_B);
        v3SetZero(tauActual_B);

        /* loop over all thrusters and compute the actual torque to be applied */
        for(i=0; i<numForces; i++)
        {
            thrusterForce = fabs(F[i]) < FMag[i] ? F[i] : FMag[i]*fabs(F[i])/F[i];
            v3Scale(thrusterForce, D[i], LrEffector_B);
            v3Add(tauActual_B, LrEffector_B, tauActual_B);
        }

        /* evaluate the angle between the requested and thruster implemented torque vector */
        v3Normalize(tauActual_B, tauActual_B);
        if(v3Dot(BLr_hat_B, tauActual_B) < 1.0)
        {
            returnAngle = acos(v3Dot(BLr_hat_B, tauActual_B));
        }
    }

    return(returnAngle);
    
}
