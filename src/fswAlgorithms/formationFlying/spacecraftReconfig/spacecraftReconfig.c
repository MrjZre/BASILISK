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

#include "spacecraftReconfig.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "simulation/utilities/linearAlgebra.h"
#include "simulation/utilities/astroConstants.h"
#include "simulation/utilities/rigidBodyKinematics.h"


/*! This method initializes the configData for this module.
 It checks to ensure that the inputs are sane and then creates the
 output message
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The Basilisk module identifier
 */
void SelfInit_spacecraftReconfig(spacecraftReconfigConfig *configData, int64_t moduleID)
{
    configData->attRefOutMsgID = CreateNewMessage(configData->attRefOutMsgName,
                                                  sizeof(AttRefFswMsg),
                                                  "AttRefFswMsg",moduleID);
    configData->onTimeOutMsgID = CreateNewMessage(configData->onTimeOutMsgName,
                                                  sizeof(THRArrayOnTimeCmdIntMsg),
                                                  "THRArrayOnTimeCmdIntMsg",moduleID);
    return;
}

/*! This method performs the second stage of initialization for this module.
 Its primary function is to link the input messages that were created elsewhere.
 Nothing else should be happening in this function.
 @return void
 @param configData The configuration data associated with this module
 @param moduleID The Basilisk module identifier
 */
void CrossInit_spacecraftReconfig(spacecraftReconfigConfig *configData, int64_t moduleID)
{
    configData->chiefTransInMsgID   = subscribeToMessage(configData->chiefTransInMsgName,
                                                         sizeof(NavTransIntMsg),moduleID);
    configData->deputyTransInMsgID  = subscribeToMessage(configData->deputyTransInMsgName,
                                                         sizeof(NavTransIntMsg),moduleID);
    configData->thrustConfigInMsgID = subscribeToMessage(configData->thrustConfigInMsgName,
                                                         sizeof(THRArrayConfigFswMsg),moduleID);
    // reference attitude message is optional
    configData->attRefInMsgID = -1;
    if(strlen(configData->attRefInMsgName) > 0) {
        configData->attRefInMsgID   = subscribeToMessage(configData->attRefInMsgName,
                                                         sizeof(AttRefFswMsg),moduleID);
    }
    return;
}

/*! This method performs a complete reset of the module.  Local module variables that retain
 time varying states between function calls are reset to their default values.  The local copy of the
 message output buffer should be cleared.
 @return void
 @param configData The configuration data associated with the module
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The Basilisk module identifier
 */
void Reset_spacecraftReconfig(spacecraftReconfigConfig *configData, uint64_t callTime, int64_t moduleID)
{
    configData->prevCallTime    = 0;
    configData->tCurrent        = 0.0;
    configData->thrustOnFlag    = 0;
    memset(&configData->dvArray[0], 0x0, sizeof(spacecraftReconfigConfigBurnInfo));
    memset(&configData->dvArray[1], 0x0, sizeof(spacecraftReconfigConfigBurnInfo));
    memset(&configData->dvArray[2], 0x0, sizeof(spacecraftReconfigConfigBurnInfo));
    return;
}

/*! Add a description of what this main Update() routine does for this module
 @return void
 @param configData The configuration data associated with the module
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The Basilisk module identifier
 */
void Update_spacecraftReconfig(spacecraftReconfigConfig *configData, uint64_t callTime, int64_t moduleID)
{
    // in
    NavTransIntMsg chiefTransMsg;
    NavTransIntMsg deputyTransMsg;
    THRArrayConfigFswMsg thrustConfigMsg;
    AttRefFswMsg attRefInMsg;
    // out
    AttRefFswMsg attRefMsg;
    THRArrayOnTimeCmdIntMsg thrustOnMsg;
    uint64_t timeOfMsgWritten;
    uint32_t sizeOfMsgWritten;
    // memset
    memset(&(chiefTransMsg), 0x0, sizeof(NavTransIntMsg));
    memset(&(deputyTransMsg), 0x0, sizeof(NavTransIntMsg));
    memset(&(thrustConfigMsg), 0x0, sizeof(THRArrayConfigFswMsg));
    memset(&(attRefInMsg), 0x0, sizeof(AttRefFswMsg));
    /*! - Read the input messages */
    ReadMessage(configData->chiefTransInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(NavTransIntMsg), (void*) &(chiefTransMsg), moduleID);
    ReadMessage(configData->deputyTransInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(NavTransIntMsg), (void*) &(deputyTransMsg), moduleID);
    ReadMessage(configData->thrustConfigInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(THRArrayConfigFswMsg), (void*) &(thrustConfigMsg), moduleID);
    if (configData->attRefInMsgID >= 0) {
        ReadMessage(configData->attRefInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                    sizeof(AttRefFswMsg), (void*) &(attRefInMsg), moduleID);
    }

    if(configData->prevCallTime == 0) {
		configData->prevCallTime = callTime; // initialize
	}
    // calculate elapsed time from last module updated time
    double elapsed_time = ((double)(callTime - configData->prevCallTime)) * NANO2SEC;
    configData->tCurrent = configData->tCurrent + elapsed_time;
	configData->prevCallTime = callTime;

    UpdateManeuver(configData, chiefTransMsg, deputyTransMsg, attRefInMsg,
                     thrustConfigMsg, &attRefMsg, &thrustOnMsg, callTime, moduleID);

    /*! - write the module output message */
    WriteMessage(configData->attRefOutMsgID, callTime,
                     sizeof(AttRefFswMsg),(void*) &(attRefMsg), moduleID);
    if(configData->thrustOnFlag == 1){
        // only when thrustOnFlag is 1, thrustOnMessage is output
        WriteMessage(configData->onTimeOutMsgID, callTime,
                     sizeof(THRArrayOnTimeCmdIntMsg),(void*) &(thrustOnMsg), moduleID);
    }
    return;
}

/*! based on burn schedule, this function creates a message of
 reference attitude and thruster on time
 @return void
 @param configData The configuration data associated with the module
 @param chiefTransMsg chief's position and velocity
 @param deputyTransMsg deputy's position and velocity
 @param attRefInMsg target attitude
 @param thrustConfigMsg thruster's config information
 @param attRefMsg target attitude
 @param thrustOnMsg thruster on time
 @param callTime The clock time at which the function was called (nanoseconds)
 @param moduleID The Basilisk module identifier
 */
void UpdateManeuver(spacecraftReconfigConfig *configData, NavTransIntMsg chiefTransMsg,
                     NavTransIntMsg deputyTransMsg, AttRefFswMsg attRefInMsg,
                     THRArrayConfigFswMsg thrustConfigMsg, AttRefFswMsg *attRefMsg,
                     THRArrayOnTimeCmdIntMsg *thrustOnMsg, uint64_t callTime, int64_t moduleID)
{
    /* conversion from r,v to classical orbital elements */
    classicElements oe_c, oe_d;
    rv2elem(configData->mu,chiefTransMsg.r_BN_N,chiefTransMsg.v_BN_N,&oe_c);
    rv2elem(configData->mu,deputyTransMsg.r_BN_N,deputyTransMsg.v_BN_N,&oe_d);

    /* schedule dv manuever at the initiation timing of this module */
    if(configData->dvArray[0].flag == 0){
        configData->resetPeriod = 2*M_PI/sqrt(configData->mu/pow(oe_c.a,3)); // one orbital period
        ScheduleDV(configData, oe_c, oe_d, thrustConfigMsg);
        // sort three burns (dvArray structures) in ascending order
        qsort(configData->dvArray, sizeof(configData->dvArray) / sizeof(configData->dvArray[0]),
              sizeof(spacecraftReconfigConfigBurnInfo), CompareTime);
    }

    /* After burn scheduling, the routine below is executed at every time step */
    /* Overall, configData->dvArray[i].flag is checked sequentially (i=0,1,2)  */
    if(configData->dvArray[0].flag == 1){
        double t_left = configData->dvArray[0].t - configData->tCurrent; // remaining time until first burn
        if(t_left > configData->attControlTime && configData->attRefInMsgID>=0){
            // in this case, there is enough time until first burn, so reference input attitude is set as target
            v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
        }else{
            // in this case, first burn attitude is set at target
            v3Copy(configData->dvArray[0].sigma_RN, attRefMsg->sigma_RN);
        }
        // middle of thruster burn duration time is located at the expected exact timing of impulsive control
        if(t_left < (int)configData->dvArray[0].thrustOnTime/(2*thrustConfigMsg.numThrusters) &&
            configData->dvArray[0].flag == 1){
            configData->thrustOnFlag     = 1; // thrustOnFlag is ON
            configData->dvArray[0].flag  = 2; // first burn is regarded as finished by setting this to 2
            int i = 0;
            for(i = 0;i < thrustConfigMsg.numThrusters;++i){
                thrustOnMsg->OnTimeRequest[i] = configData->dvArray[0].thrustOnTime/thrustConfigMsg.numThrusters;
            }
        }else{
            configData->thrustOnFlag = 0; // thrustOnFlag is OFF
        }
    }else if(configData->dvArray[1].flag == 1) {
        double t_left = configData->dvArray[1].t - configData->tCurrent; // remaining time until second burn
        if(configData->dvArray[0].flag == 2 && 
           configData->tCurrent < (configData->dvArray[0].t+configData->dvArray[0].thrustOnTime/(2*thrustConfigMsg.numThrusters))){
            // in this case, first burn is still executed, so first burn attitude is set as target
            v3Copy(configData->dvArray[0].sigma_RN, attRefMsg->sigma_RN);
        }else if(t_left > configData->attControlTime && configData->attRefInMsgID>=0){
            // in this case, there is enough time until second burn, so reference input attitude is set as target
            v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
        }else{
            // in this case, second burn attitude is set at target
            v3Copy(configData->dvArray[1].sigma_RN, attRefMsg->sigma_RN);
        }
        if(t_left < (int)configData->dvArray[1].thrustOnTime/(2*thrustConfigMsg.numThrusters) &&
           configData->dvArray[1].flag == 1){
            configData->thrustOnFlag = 1;
            configData->dvArray[1].flag = 2;
            int i = 0;
            for(i = 0;i < thrustConfigMsg.numThrusters;++i){
                thrustOnMsg->OnTimeRequest[i] = configData->dvArray[1].thrustOnTime/thrustConfigMsg.numThrusters;
            }
        }else{
            configData->thrustOnFlag = 0;
        }
    }else if(configData->dvArray[2].flag == 1){
        double t_left = configData->dvArray[2].t - configData->tCurrent; // remaining time until third burn
        if(configData->dvArray[1].flag == 2 && 
           configData->tCurrent < (configData->dvArray[1].t+configData->dvArray[1].thrustOnTime/(2*thrustConfigMsg.numThrusters))){
            // in this case, second burn is still executed, so second burn attitude is set as target
            v3Copy(configData->dvArray[1].sigma_RN, attRefMsg->sigma_RN);
        }else if(configData->dvArray[0].flag == 2 && 
           configData->tCurrent < (configData->dvArray[0].t+configData->dvArray[0].thrustOnTime/(2*thrustConfigMsg.numThrusters))){
            // in this case, first burn is still executed, so first burn attitude is set as target
            v3Copy(configData->dvArray[0].sigma_RN, attRefMsg->sigma_RN);
        }else if(t_left > configData->attControlTime && configData->attRefInMsgID>=0){
            // in this case, there is enough time until second burn, so reference input attitude is set as target
            v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
        }else{
            // in this case, third burn attitude is set at target
            v3Copy(configData->dvArray[2].sigma_RN, attRefMsg->sigma_RN);
        }
        if(t_left < (int)configData->dvArray[2].thrustOnTime/(2*thrustConfigMsg.numThrusters) &&
           configData->dvArray[2].flag == 1){
            configData->thrustOnFlag = 1;
            configData->dvArray[2].flag = 2;
            int i = 0;
            for(i = 0;i < thrustConfigMsg.numThrusters;++i){
                thrustOnMsg->OnTimeRequest[i] = configData->dvArray[2].thrustOnTime/thrustConfigMsg.numThrusters;
            }
        }else{
            configData->thrustOnFlag = 0;
        }
    }else{
        // this section is valid when all the impulses are finished
        // we have to consider a case when one dvArray[].flag is set to 3, which means that the burn is combined with another
        if(configData->dvArray[2].flag == 2){
            if(configData->tCurrent > (configData->dvArray[2].t+configData->dvArray[2].thrustOnTime/(2*thrustConfigMsg.numThrusters)) &&
               configData->attRefInMsgID>=0){
                v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
            }else{
                v3Copy(configData->dvArray[2].sigma_RN, attRefMsg->sigma_RN);
            }
        }else if(configData->dvArray[1].flag == 2){
            if(configData->tCurrent > (configData->dvArray[1].t+configData->dvArray[1].thrustOnTime/(2*thrustConfigMsg.numThrusters)) &&
               configData->attRefInMsgID>=0){
                v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
            }else{
                v3Copy(configData->dvArray[1].sigma_RN, attRefMsg->sigma_RN);
            }  
        }else if(configData->dvArray[0].flag == 2){
            if(configData->tCurrent > (configData->dvArray[0].t+configData->dvArray[0].thrustOnTime/(2*thrustConfigMsg.numThrusters)) &&
               configData->attRefInMsgID>=0){
                v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
            }else{
                v3Copy(configData->dvArray[0].sigma_RN, attRefMsg->sigma_RN);
            }
        }else{
            v3Copy(attRefInMsg.sigma_RN, attRefMsg->sigma_RN);
        }
        configData->thrustOnFlag = 0;
    }

    // at the end of one orbital period, reset this module
    if(configData->tCurrent > configData->resetPeriod){
        Reset_spacecraftReconfig(configData, callTime, moduleID);
    }
    // omega and domega reference attitude (set to zero)
    double omega_RN[3] = {0,0,0};
    double domega_RN[3] = {0,0,0};
    v3Copy(omega_RN, attRefMsg->omega_RN_N);
    v3Copy(domega_RN, attRefMsg->domega_RN_N);
    return;
}

/*! This function is used to adjust a certain value in a certain range between lower threshold and upper threshold.
 This function is particularily used to adjsut angles used in orbital motions such as True Anomaly, Mean Anomaly, and so on.
 @return double
 @param lower lower threshold
 @param upper upper threshold
 @param angle an angle which you want to be between lower and upper
*/
double AdjustRange(double lower, double upper, double angle)
{
    if(upper < lower){
        printf("illegal parameters\n");
        return -1;
    }
    double width = upper - lower;
    double adjusted_angle = angle;
    while (adjusted_angle > upper){
        adjusted_angle = adjusted_angle - width;
    }
    while (adjusted_angle < lower){
        adjusted_angle = adjusted_angle + width;
    }
    return adjusted_angle;
}

/*! This function is used to sort an array of
 spacecraftReconfigConfigBurnInfo in ascending order.
 @return void
 @param n1
 @param n2
 */
int CompareTime(const void * n1, const void * n2)
{
	if (((spacecraftReconfigConfigBurnInfo *)n1)->t > ((spacecraftReconfigConfigBurnInfo *)n2)->t)
	{
		return 1;
	}
	else if (((spacecraftReconfigConfigBurnInfo *)n1)->t < ((spacecraftReconfigConfigBurnInfo *)n2)->t)
	{
		return -1;
	}
	else
	{
		return 0;
	}
}

/*! This function is used to sort an array of
 spacecraftReconfigConfigBurnInfo in ascending order.
 @return void
 @param configData The configuration data associated with this module
 @param oe_c chief's orbital element
 @param oe_d deputy's orbital element
 @param thrustConfigMsg
 */
void ScheduleDV(spacecraftReconfigConfig *configData,classicElements oe_c,
                          classicElements oe_d, THRArrayConfigFswMsg thrustConfigMsg)
{
    // calculation necessary variables
    double da     = oe_d.a - oe_c.a;
    double de     = oe_d.e - oe_c.e;
    double di     = oe_d.i - oe_c.i;
    di            = AdjustRange(-M_PI, M_PI, di);
    double domega = oe_d.omega - oe_c.omega;
    double dOmega = oe_d.Omega - oe_c.Omega;
    dOmega        = AdjustRange(-M_PI, M_PI, dOmega);
    domega        = AdjustRange(-M_PI, M_PI, domega);
    double E_c    = f2E(oe_c.f, oe_c.e);
    double M_c    = E2M(E_c, oe_c.e);
    M_c           = AdjustRange(0, 2*M_PI, M_c);
    double E_d    = f2E(oe_d.f, oe_d.e);
    double M_d    = E2M(E_d, oe_d.e);
    M_d           = AdjustRange(0, 2*M_PI, M_d);
    double dM     = M_d - M_c;
    dM            = AdjustRange(-M_PI, M_PI, dM);
    double n      = sqrt(configData->mu/(oe_c.a*oe_c.a*oe_c.a));
    double eta    = sqrt(1.0-oe_c.e*oe_c.e);
    double p      = oe_c.a*(1.0-oe_c.e*oe_c.e);
    double h      = n*oe_c.a*oe_c.a*eta;
    double rp     = oe_c.a*(1.0-oe_c.e);
    double ra     = oe_c.a*(1.0+oe_c.e);

    da     = da     - configData->targetClassicOED[0];
    di     = di     - configData->targetClassicOED[2];
    de     = de     - configData->targetClassicOED[1];
    dOmega = dOmega - configData->targetClassicOED[3];
    domega = domega - configData->targetClassicOED[4];
    dM     = dM     - configData->targetClassicOED[5];

    /* calculation below is divided into two parts */
    /* 1. calculate dV maneuver timing in tangential and radial direction at perigee */
    /* 2. calculate dV maneuver timing in tangential and radial direction at apogee  */
    /* 3. calculate dV maneuver timing in normal direction */
    /* 4. calculate dV magnitude for each burn */
    /* 5. calculate thrustOnTime */

    // 1. calculate t_dvrtp
    double f_c_dvrtp = 0.0; // f = 0 @ perigee
    double E_c_dvrtp = f2E(f_c_dvrtp, oe_c.e);
    double M_c_dvrtp = E2M(E_c_dvrtp, oe_c.e);
    M_c_dvrtp        = AdjustRange(0, 2*M_PI, M_c_dvrtp);
    if(M_c_dvrtp > M_c){
        configData->dvArray[0].t = (M_c_dvrtp - M_c)/n;
    }else{
        configData->dvArray[0].t = (2*M_PI + M_c_dvrtp - M_c)/n;
    }
    // 2. calculate t_dvrta
    double f_c_dvrta = M_PI; // f = pi @ apogee
    double E_c_dvrta = f2E(f_c_dvrta, oe_c.e);
    double M_c_dvrta = E2M(E_c_dvrta, oe_c.e);
    M_c_dvrta        = AdjustRange(0, 2*M_PI, M_c_dvrta);
    if(M_c_dvrta > M_c){
        configData->dvArray[1].t = (M_c_dvrta - M_c)/n;
    }else{
        configData->dvArray[1].t = (2*M_PI + M_c_dvrta - M_c)/n;
    }
    // 3. calculate t_dvn
    double theta_c     = oe_c.omega + oe_c.f;
    theta_c            = AdjustRange(0, 2*M_PI, theta_c);
    double theta_c_dvn = atan2((-dOmega)*sin(oe_c.i), (-di));
    // choose burn lattitude angle so that dV is +z direction in LVLH
    if((-di)*cos(theta_c_dvn)<0 && (-dOmega)*sin(oe_c.i)*sin(theta_c_dvn) <0){
        theta_c_dvn = theta_c_dvn + M_PI;
    }
    theta_c_dvn    = AdjustRange(0, 2*M_PI, theta_c_dvn);
    double f_c_dvn = theta_c_dvn - oe_c.omega;
    double E_c_dvn = f2E(f_c_dvn, oe_c.e);
    double M_c_dvn = E2M(E_c_dvn, oe_c.e);
    M_c_dvn        = AdjustRange(0, 2*M_PI, M_c_dvn);
    if(M_c_dvn > M_c){
        configData->dvArray[2].t = (M_c_dvn - M_c)/n;
    }else{
        configData->dvArray[2].t = (2*M_PI + M_c_dvn - M_c)/n;
    }
    // 4. calculate dvrp_mag, dvtp_mag, dvra_mag, dvta_mag, dvn_mag
    double dvtp_mag = n*oe_c.a*eta/4.0*((-da)/oe_c.a + (-de)/(1.0+oe_c.e));
    double dvta_mag = n*oe_c.a*eta/4.0*((-da)/oe_c.a - (-de)/(1.0-oe_c.e));
    // compensate drift of dM caused by initial da
    if(configData->dvArray[0].t < configData->dvArray[1].t){
        dM = dM
           - 3.0/2.0*n/oe_c.a*da*configData->dvArray[0].t
           - 3.0/2.0*n/oe_c.a*(da+2.0*oe_c.a*oe_c.a/h*p/rp*dvtp_mag)*(configData->dvArray[1].t - configData->dvArray[0].t);
    }else{
        dM = dM
           - 3.0/2.0*n/oe_c.a*da*configData->dvArray[1].t
           - 3.0/2.0*n/oe_c.a*(da+2.0*oe_c.a*oe_c.a/h*p/ra*dvta_mag)*(configData->dvArray[0].t - configData->dvArray[1].t);
    }
    double dvrp_mag = -n*oe_c.a/4*(pow(1+oe_c.e,2)/eta*((-domega)+(-dOmega)*cos(oe_c.i)) + (-dM));
    double dvra_mag = -n*oe_c.a/4*(pow(1-oe_c.e,2)/eta*((-domega)+(-dOmega)*cos(oe_c.i)) + (-dM));
    double r_dvn = p/(1+oe_c.e*cos(f_c_dvn));
    double dvn_mag = h/r_dvn*sqrt(pow((-di),2) + pow((-dOmega)*sin(oe_c.i),2));
    // 5. calculate thrustOnTime
    // if timings of any two burns are close to each other, they are combined into one burn
    if(configData->dvArray[2].t - configData->dvArray[0].t < configData->attControlTime &&
       configData->dvArray[0].t - configData->dvArray[2].t < configData->attControlTime){
        configData->dvArray[0].thrustOnTime = sqrt(dvrp_mag*dvrp_mag+dvtp_mag*dvtp_mag+dvn_mag*dvn_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[1].thrustOnTime = sqrt(dvra_mag*dvra_mag+dvta_mag*dvta_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[2].thrustOnTime = 0.0;
        configData->dvArray[2].flag = 3;
    }else if(configData->dvArray[2].t - configData->dvArray[1].t < configData->attControlTime &&
             configData->dvArray[1].t - configData->dvArray[2].t < configData->attControlTime){
        configData->dvArray[0].thrustOnTime = sqrt(dvrp_mag*dvrp_mag+dvtp_mag*dvtp_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[1].thrustOnTime = sqrt(dvra_mag*dvra_mag+dvta_mag*dvta_mag+dvn_mag*dvn_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[2].thrustOnTime = 0.0;
        configData->dvArray[2].flag = 3;
    }else{
        configData->dvArray[0].thrustOnTime = sqrt(dvrp_mag*dvrp_mag+dvtp_mag*dvtp_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[1].thrustOnTime = sqrt(dvra_mag*dvra_mag+dvta_mag*dvta_mag)*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
        configData->dvArray[2].thrustOnTime = dvn_mag*configData->scMassDeputy/thrustConfigMsg.thrusters[0].maxThrust;
    }
    // if thrustOnTime is smaller than a cerain threshold, the impulse is neglected
    // 1.0 second is temporarily set as threshold regarding whether small impulse is neglected or not
    if(configData->dvArray[0].thrustOnTime/thrustConfigMsg.numThrusters < 1.0){
        configData->dvArray[0].flag = 3;
    }
    if(configData->dvArray[1].thrustOnTime/thrustConfigMsg.numThrusters < 1.0){
        configData->dvArray[1].flag = 3;
    }
    if(configData->dvArray[2].thrustOnTime/thrustConfigMsg.numThrusters < 1.0){
        configData->dvArray[2].flag = 3;
    }

    /* below is calculation of target sigma for three burns */
    /* R frame represents a frame where scheduled thrusct direction is aligned with +Z axis */
    /* dcm_TR is used to align scheduled thrust direction with configured thruster direction */
    /* by multiplying two dcms dcm_TR and dcm_RN, target attitude is calculated */
    
    /* calculate dcm_TR (this is common in three burns) */
    double thruster_dir[3];
    double ep_vec[3];
    double ez[3] = {0.0,0.0,1.0};
    v3Normalize(thrustConfigMsg.thrusters[0].tHatThrust_B,thruster_dir);
    if(thruster_dir[0] == 0.0 && thruster_dir[1] == 0.0){
        // can be any vector in XY-plane
        ep_vec[0] = 1.0;
        ep_vec[1] = 0.0;
        ep_vec[2] = 0.0;
    }else{
        v3Cross(thruster_dir,ez,ep_vec);
    }
    v3Normalize(ep_vec,ep_vec);
    double cos_dv = v3Dot(thruster_dir,ez);
    double acos_dv = acos(cos_dv);
    double ep_TR[4] = {cos(acos_dv/2.0),ep_vec[0]*sin(acos_dv/2.0),ep_vec[1]*sin(acos_dv/2.0),ep_vec[2]*sin(acos_dv/2.0)};
    double dcm_TR[3][3];
    EP2C(ep_TR,dcm_TR);
    
    /* calculate sigma_dvrtp_RN */
    // calculate dcm_RN
    double M_d_dvrtp = M_d + configData->dvArray[0].t*n;
    double E_d_dvrtp = M2E(M_d_dvrtp, oe_d.e);
    double f_d_dvrtp = E2f(E_d_dvrtp, oe_d.e);
    classicElements oe_d_dvrtp;
    oe_d_dvrtp   = oe_d;
    oe_d_dvrtp.f = f_d_dvrtp;
    double rVec_d_dvrtp[3], vVec_d_dvrtp[3], hVec_d_dvrtp[3],tVec_d_dvrtp[3];
    elem2rv(configData->mu, &oe_d_dvrtp, rVec_d_dvrtp, vVec_d_dvrtp);
    v3Cross(rVec_d_dvrtp, vVec_d_dvrtp, hVec_d_dvrtp);
    v3Cross(hVec_d_dvrtp, rVec_d_dvrtp, tVec_d_dvrtp);
    v3Normalize(rVec_d_dvrtp,rVec_d_dvrtp);
    v3Scale(dvrp_mag,rVec_d_dvrtp,rVec_d_dvrtp);
    v3Normalize(tVec_d_dvrtp,tVec_d_dvrtp);
    v3Scale(dvtp_mag,tVec_d_dvrtp,tVec_d_dvrtp);
    double thrustVec_dvrtp[3];
    // sum of scalalized two vectors in tangential and radial directions
    v3Add(rVec_d_dvrtp,tVec_d_dvrtp,thrustVec_dvrtp);
    // in case two burns are combined, target attitude also has to be adjusted
    if(configData->dvArray[2].t - configData->dvArray[0].t < configData->attControlTime &&
       configData->dvArray[0].t - configData->dvArray[2].t < configData->attControlTime){
        v3Normalize(hVec_d_dvrtp,hVec_d_dvrtp);
        v3Scale(dvn_mag,hVec_d_dvrtp,hVec_d_dvrtp);
        // add normal direction vector
        v3Add(thrustVec_dvrtp,hVec_d_dvrtp,thrustVec_dvrtp);
        v3Cross(thrustVec_dvrtp, hVec_d_dvrtp, hVec_d_dvrtp);
    }
    double dcm_RN_dvrtp[3][3];
    v3Normalize(thrustVec_dvrtp, dcm_RN_dvrtp[2]);
    v3Normalize(hVec_d_dvrtp, dcm_RN_dvrtp[1]);
    v3Cross(dcm_RN_dvrtp[1], dcm_RN_dvrtp[2], dcm_RN_dvrtp[0]);
    // calculate dcm_TN = dcm_TR * dcm_RN
    double dcm_TN_dvrtp[3][3];
    m33MultM33(dcm_TR,dcm_RN_dvrtp,dcm_TN_dvrtp);
    C2MRP(dcm_TN_dvrtp, configData->dvArray[0].sigma_RN);
    
    /* calculate sigma_dvrta_RN */
    double M_d_dvrta = M_d + configData->dvArray[1].t*n;
    double E_d_dvrta = M2E(M_d_dvrta, oe_d.e);
    double f_d_dvrta = E2f(E_d_dvrta, oe_d.e);
    classicElements oe_d_dvrta;
    oe_d_dvrta   = oe_d;
    oe_d_dvrta.f = f_d_dvrta;
    double rVec_d_dvrta[3], vVec_d_dvrta[3], hVec_d_dvrta[3],tVec_d_dvrta[3];
    elem2rv(configData->mu, &oe_d_dvrta, rVec_d_dvrta, vVec_d_dvrta);
    v3Cross(rVec_d_dvrta, vVec_d_dvrta, hVec_d_dvrta);
    v3Cross(hVec_d_dvrta, rVec_d_dvrta, tVec_d_dvrta);
    v3Normalize(rVec_d_dvrta,rVec_d_dvrta);
    v3Scale(dvra_mag,rVec_d_dvrta,rVec_d_dvrta);
    v3Normalize(tVec_d_dvrta,tVec_d_dvrta);
    v3Scale(dvta_mag,tVec_d_dvrta,tVec_d_dvrta);
    double thrustVec_dvrta[3];
    // sum of scalalized two vectors in tangential and radial directions
    v3Add(rVec_d_dvrta,tVec_d_dvrta,thrustVec_dvrta);
    // in case two burns are combined, target attitude also has to be adjusted
    if(configData->dvArray[2].t - configData->dvArray[1].t < configData->attControlTime &&
       configData->dvArray[1].t - configData->dvArray[2].t < configData->attControlTime){
        v3Normalize(hVec_d_dvrta,hVec_d_dvrta);
        v3Scale(dvn_mag,hVec_d_dvrta,hVec_d_dvrta);
        // add normal direction vector
        v3Add(thrustVec_dvrta,hVec_d_dvrta,thrustVec_dvrta);
        v3Cross(thrustVec_dvrta, hVec_d_dvrta, hVec_d_dvrta);
    }
    double dcm_RN_dvrta[3][3];
    v3Normalize(thrustVec_dvrta, dcm_RN_dvrta[2]);
    v3Normalize(hVec_d_dvrta, dcm_RN_dvrta[1]);
    v3Cross(dcm_RN_dvrta[1], dcm_RN_dvrta[2], dcm_RN_dvrta[0]);
    // calculate dcm_TN = dcm_TR * dcm_RN
    double dcm_TN_dvrta[3][3];
    m33MultM33(dcm_TR,dcm_RN_dvrta,dcm_TN_dvrta);
    C2MRP(dcm_TN_dvrta, configData->dvArray[1].sigma_RN);
    
    /* calculate sigma_dvn_RN */
    double M_d_dvn = M_d + configData->dvArray[2].t*n;
    double E_d_dvn = M2E(M_d_dvn, oe_d.e);
    double f_d_dvn = E2f(E_d_dvn, oe_d.e);
    classicElements oe_d_dvn;
    oe_d_dvn = oe_d;
    oe_d_dvn.f = f_d_dvn;
    double rVec_d_dvn[3], vVec_d_dvn[3], hVec_d_dvn[3];
    double dcm_RN[3][3];
    elem2rv(configData->mu, &oe_d_dvn, rVec_d_dvn, vVec_d_dvn);
    v3Normalize(rVec_d_dvn, dcm_RN[0]);
    v3Cross(rVec_d_dvn, vVec_d_dvn, hVec_d_dvn);
    // normal direction is thrust direction
    v3Normalize(hVec_d_dvn, dcm_RN[2]);
    v3Cross(dcm_RN[2], dcm_RN[0], dcm_RN[1]);
    if(configData->dvArray[2].t - configData->dvArray[0].t < configData->attControlTime &&
       configData->dvArray[0].t - configData->dvArray[2].t < configData->attControlTime){
        C2MRP(dcm_TN_dvrtp, configData->dvArray[2].sigma_RN);
    }else if(configData->dvArray[2].t - configData->dvArray[1].t < configData->attControlTime &&
             configData->dvArray[1].t - configData->dvArray[2].t < configData->attControlTime){
        C2MRP(dcm_TN_dvrta, configData->dvArray[2].sigma_RN);
    }else{
        // calculate dcm_TN = dcm_TR * dcm_RN
        double dcm_TN_dvn[3][3];
        m33MultM33(dcm_TR,dcm_RN,dcm_TN_dvn);
        C2MRP(dcm_TN_dvn, configData->dvArray[2].sigma_RN);
    }

    // if each dV is scheduled (and not skipped), then set flag to 1
    if(configData->dvArray[0].flag == 0){
        configData->dvArray[0].flag = 1;
    }
    if(configData->dvArray[1].flag == 0){
        configData->dvArray[1].flag = 1;
    }
    if(configData->dvArray[2].flag == 0){
        configData->dvArray[2].flag = 1;
    }
}
