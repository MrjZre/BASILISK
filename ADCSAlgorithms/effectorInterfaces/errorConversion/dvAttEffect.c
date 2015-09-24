
#include "effectorInterfaces/errorConversion/dvAttEffect.h"
#include "attControl/vehControlOut.h"
#include "SimCode/utilities/linearAlgebra.h"
#include "SimCode/utilities/rigidBodyKinematics.h"
#include "sensorInterfaces/IMUSensorData/imuComm.h"
#include <string.h>
#include <math.h>

/*! This method initializes the ConfigData for the sun safe ACS control.
 It checks to ensure that the inputs are sane and then creates the
 output message
 @return void
 @param ConfigData The configuration data associated with the sun safe control
 */
void SelfInit_dvAttEffect(dvAttEffectConfig *ConfigData)
{
    uint32_t i;
    /*! Begin method steps */
    /*! - Loop over number of thruster blocks and create output messages */
    for(i=0; i<ConfigData->numThrGroups; i=i+1)
    {
        ConfigData->thrGroups[i].outputMsgID = CreateNewMessage(
            ConfigData->thrGroups[i].outputDataName, sizeof(vehEffectorOut),
            "vehEffectorOut");
    }
 
    
}

/*! This method performs the second stage of initialization for the sun safe ACS
 interface.  It's primary function is to link the input messages that were
 created elsewhere.
 @return void
 @param ConfigData The configuration data associated with the sun safe ACS control
 */
void CrossInit_dvAttEffect(dvAttEffectConfig *ConfigData)
{
    /*! - Get the control data message ID*/
    ConfigData->inputMsgID = FindMessageID(ConfigData->inputControlName);
    
}

/*! This method takes the estimated body-observed sun vector and computes the
 current attitude/attitude rate errors to pass on to control.
 @return void
 @param ConfigData The configuration data associated with the sun safe ACS control
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Update_dvAttEffect(dvAttEffectConfig *ConfigData, uint64_t callTime)
{

    uint64_t ClockTime;
    uint32_t ReadSize;
    uint32_t i;
    vehControlOut cntrRequest;
    
    /*! Begin method steps*/
    /*! - Read the input requested torque from the feedback controller*/
    ReadMessage(ConfigData->inputMsgID, &ClockTime, &ReadSize,
                sizeof(vehControlOut), (void*) &(cntrRequest));
    
    for(i=0; i<ConfigData->numThrGroups; i=i+1)
    {
        computeSingleThrustBlock(&(ConfigData->thrGroups[i]), callTime,
            &cntrRequest);
    }
    
    return;
}

void computeSingleThrustBlock(ThrustGroupData *thrData, uint64_t callTime,
vehControlOut *contrReq)
{
    double unSortOnTime[MAX_NUM_EFFECTORS];
    effPairs unSortPairs[MAX_NUM_EFFECTORS];
    effPairs sortPairs[MAX_NUM_EFFECTORS];
    uint32_t i;
    double localRequest[3];
    
    /*! Begin method steps*/
    v3Scale(-1.0, contrReq->accelRequestBody, localRequest);
    mMultV(thrData->thrOnMap, thrData->numEffectors, 3,
           localRequest, unSortOnTime);
    
    for(i=0; i<thrData->numEffectors; i=i+1)
    {
        unSortOnTime[i] = unSortOnTime[i] + thrData->nomThrustOn;
    }
    
    for(i=0; i<thrData->numEffectors; i=i+1)
    {
        if(unSortOnTime[i] < thrData->minThrustRequest)
        {
            unSortOnTime[i] = 0.0;
        }
    }
    
    for(i=0; i<thrData->numEffectors; i++)
    {
        unSortPairs[i].onTime = unSortOnTime[i];
        unSortPairs[i].thrustIndex = i;
    }
    effectorVSort(unSortPairs, sortPairs, thrData->numEffectors);
    memset(thrData->cmdRequests.effectorRequest, 0x0,
           MAX_NUM_EFFECTORS*sizeof(double));
    for(i=0; i<thrData->maxNumCmds; i=i+1)
    {
        thrData->cmdRequests.effectorRequest[sortPairs[i].thrustIndex] =
        sortPairs[i].onTime;
    }
    WriteMessage(thrData->outputMsgID, callTime, sizeof(vehEffectorOut),
                 (void*) &(thrData->cmdRequests));
}

void effectorVSort(effPairs *Input, effPairs *Output, size_t dim)
{
    int i, j;
    int Swapped;
    Swapped = 1;
    memcpy(Output, Input, dim*sizeof(effPairs));
    for(i=0; i<dim && Swapped > 0; i++)
    {
        Swapped = 0;
        for(j=0; j<dim-1; j++)
        {
            if(Output[j].onTime<Output[j+1].onTime)
            {
                double tempOn = Output[j+1].onTime;
                uint32_t tempIndex = Output[j+1].thrustIndex;
                Output[j+1].onTime = Output[j].onTime;
                Output[j+1].thrustIndex = Output[j].thrustIndex;
                Output[j].onTime = tempOn;
                Output[j].thrustIndex = tempIndex;
                Swapped = 1;
            }
        }
    }
}
