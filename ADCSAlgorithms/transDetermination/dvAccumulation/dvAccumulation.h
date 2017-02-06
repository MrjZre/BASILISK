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

#ifndef _DV_ACCUMULATION_H_
#define _DV_ACCUMULATION_H_

#include "messaging/static_messaging.h"
#include "../SimFswInterface/navTransMessage.h"

#define MAX_ACC_BUF_PKT 25

typedef struct {
    uint64_t measTime;                /*!< [Tick] Measurement time for accel */
    double gyro_Pltf[3];              /*!< [r/s] Angular rate measurement from gyro*/
    double accel_Pltf[3];             /*!< [m/s2] Acceleration in platform frame */
}AccPktData;

typedef struct {
    AccPktData accPkts[MAX_ACC_BUF_PKT]; /*! [-] Accelerometer buffer read in*/
}AccMsgData;

/*! @brief Top level structure for the CSS sensor interface system.  Contains all parameters for the
 CSS interface*/
typedef struct {
    char outputNavName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output message*/
    char accPktInMsgName[MAX_STAT_MSG_LENGTH]; /*!< [-] The name of the input accelerometer message*/
    uint32_t msgCount;      /*!< [-] The total number of messages read from inputs */
    double dcm_SPltf[3*3];  /*!< [-] The dcm representing the transformation from platform to structure*/
    uint64_t previousTime;  /*!< [ns] The clock time associated with the previous run of algorithm*/
 
    int32_t outputNavMsgID;    /*!< [-] The ID associated with the outgoing message*/
    int32_t accPktInMsgID;     /*!< [-] The ID associated with the incoming accelerometer buffer*/
    
    NavTransMessage outputData; /*!< [-] The local storage of the outgoing message data*/
}DVAccumulationData;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_dvAccumulation(DVAccumulationData *ConfigData, uint64_t moduleID);
    void CrossInit_dvAccumulation(DVAccumulationData *ConfigData, uint64_t moduleID);
    void Update_dvAccumulation(DVAccumulationData *ConfigData, uint64_t callTime,
        uint64_t moduleID);
    
#ifdef __cplusplus
}
#endif

/*! @} */

#endif
