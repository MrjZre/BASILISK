/*
 ISC License

 Copyright (c) 2016-2017, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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

#ifndef _ATT_MNVR_POINT_H_
#define _ATT_MNVR_POINT_H_

#include "messaging/static_messaging.h"
#include "attDetermination/CSSEst/cssWlsEst.h"
#include "attGuidance/_GeneralModuleFiles/attGuidOut.h"
#include "../SimFswInterface/navAttMessage.h"
#include <stdint.h>

/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*! @brief Top level structure for the nominal attitude maneuver guidance routine.*/
typedef struct {
    char outputDataName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output message*/
    char inputNavStateName[MAX_STAT_MSG_LENGTH]; /*!< The name of the Input message*/
    char inputAttCmdName[MAX_STAT_MSG_LENGTH]; /*<! The name of the incoming attitude command*/
    double zeroAngleTol;     /*!< r  The pointing error level to trigger maneuver on*/
    double mnvrCruiseRate;   /*!< r/s The rate at which we will slew the spacecraft*/
    double attMnvrVec[3];    /*!< -- The eigen axis that we want to rotate on to get to target*/
    double sigmaCmd[3];      /*!< -- The current attitude state command*/
    double bodyRateCmd[3];   /*!< r/s The current body rate state command*/
    double totalMnvrTime;    /*!< s  The time it will take to maneuver the spacecraft*/
    double currMnvrTime;     /*!< s  The amount of time we've been maneuvering*/
    double mnvrStartTime;    /*!< s  The amount of time to spend accelerating into maneuver*/
    uint64_t startClockRead; /*!< ns the value of the previous clock read from the last call*/
    double maxAngAccel;      /*!< r/s2 The maximum angular acceleration to take spacecraft through*/
	int32_t mnvrComplete;    /*!< (-) Helpful flag indicating if the current maneuver is complete*/
    int32_t mnvrActive;      /*!< -- Flag indicating if we are maneuvering */
    int32_t outputMsgID;     /*!< -- ID for the outgoing body estimate message*/
    int32_t inputNavID;      /*!< -- ID for the incoming nav state message*/
    int32_t inputCmdID;      /*!< -- ID for the incoming attitude command message*/
    attGuidOut attOut;       /*!< -- The output data that we compute*/
}attMnvrPointConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_attMnvrPoint(attMnvrPointConfig *ConfigData, uint64_t moduleID);
    void CrossInit_attMnvrPoint(attMnvrPointConfig *ConfigData, uint64_t moduleID);
    void Update_attMnvrPoint(attMnvrPointConfig *ConfigData, uint64_t callTime,
        uint64_t moduleID);
    void computeNewAttMnvr(attMnvrPointConfig *ConfigData, attCmdOut *endState,
        NavAttMessage *currState);
    
#ifdef __cplusplus
}
#endif

/*! @} */

#endif
