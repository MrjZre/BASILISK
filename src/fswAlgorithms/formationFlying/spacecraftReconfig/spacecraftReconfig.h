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

#ifndef _SPACECRAFT_RECONFIG_H_
#define _SPACECRAFT_RECONFIG_H_

#include <stdint.h>

#include "../dist3/autoSource/cMsgCInterface/NavTransMsg_C.h"
#include "../dist3/autoSource/cMsgCInterface/THRArrayConfigMsg_C.h"
#include "../dist3/autoSource/cMsgCInterface/AttRefMsg_C.h"
#include "../dist3/autoSource/cMsgCInterface/THRArrayOnTimeCmdMsg_C.h"

#include "simulation/utilities/bskLogging.h"
#include "simulation/utilities/orbitalMotion.h"

/*! @brief Local module specific data structure */
typedef struct {
    uint8_t flag;        //!< 0:not scheduled yet, 1:not burned yet, 2:already burned, 3:skipped (combined with another burn)
    double t;            //!< when to burn [s]
    double thrustOnTime; //!< thrust on duration time [s]
    double sigma_RN[3];  //!< target attitude
}spacecraftReconfigConfigBurnInfo;

/*! @brief Data structure for the MRP feedback attitude control routine. */
typedef struct {
    /* declare module IO interfaces */
    // in
    NavTransMsg_C chiefTransInMsg;                      //!< chief orbit input msg
    NavTransMsg_C deputyTransInMsg;                     //!< deputy orbit input msg
    THRArrayConfigMsg_C thrustConfigInMsg;              //!< THR configuration input msg
    AttRefMsg_C attRefInMsg;                            //!< nominal attitude reference input msg

    // out
    AttRefMsg_C attRefOutMsg;                           //!< attitude reference output msg
    THRArrayOnTimeCmdMsg_C onTimeOutMsg;                //!< THR on-time output msg

    double mu;  //!< [m^3/s^2] gravity constant of planet being orbited
    double attControlTime; //!< [s] attitude control margin time (time necessary to change sc's attitude)
    double targetClassicOED[6]; //!< target classic orital element difference, SMA should be normalized
    double resetPeriod; //!< [s] burn scheduling reset period
    double scMassDeputy; //!< [kg] deputy SC mass
    double tCurrent; //!< [s] timer
    uint64_t prevCallTime; //!< [ns]
    uint8_t thrustOnFlag; //!< thrust control
    int    attRefInIsLinked;        //!< flag if the attitude reference input message is linked
    spacecraftReconfigConfigBurnInfo dvArray[3];    //!< array of burns
}spacecraftReconfigConfig;

#ifdef __cplusplus
extern "C" {
#endif
    void SelfInit_spacecraftReconfig(spacecraftReconfigConfig *configData, int64_t moduleID);
    void CrossInit_spacecraftReconfig(spacecraftReconfigConfig *configData, int64_t moduleID);
    void Update_spacecraftReconfig(spacecraftReconfigConfig *configData, uint64_t callTime, int64_t moduleID);
    void Reset_spacecraftReconfig(spacecraftReconfigConfig *configData, uint64_t callTime, int64_t moduleID);

    void UpdateManeuver(spacecraftReconfigConfig *configData, NavTransMsgPayload chiefTransMsg,
                             NavTransMsgPayload deputyTransMsg, AttRefMsgPayload attRefInMsg,
                             THRArrayConfigMsgPayload thrustConfigMsg, AttRefMsgPayload *attRefMsg,
                             THRArrayOnTimeCmdMsgPayload *thrustOnMsg, uint64_t callTime, int64_t moduleID);
    double AdjustRange(double lower, double upper, double angle);
    int CompareTime(const void * n1, const void * n2);
    void ScheduleDV(spacecraftReconfigConfig *configData, classicElements oe_c,
                         classicElements oe_d, THRArrayConfigMsgPayload thrustConfigMsg);

#ifdef __cplusplus
}
#endif

#endif
