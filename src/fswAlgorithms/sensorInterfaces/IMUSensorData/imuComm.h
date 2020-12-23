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

#ifndef _IMU_COMM_H_
#define _IMU_COMM_H_

#include "cMsgCInterface/IMUSensorBodyMsg_C.h"
#include "cMsgCInterface/IMUSensorMsg_C.h"

#include "architecture/utilities/bskLogging.h"



/*! @brief module configuration message */
typedef struct {
    double dcm_BP[9];    /*!< Row major platform 2 bdy DCM*/
    IMUSensorMsg_C imuComInMsg;             /*!< imu input message*/
    IMUSensorBodyMsg_C imuSensorOutMsg;     /*!< imu output message*/

    IMUSensorBodyMsgPayload outMsgBuffer; /*!< Output data structure*/
    BSKLogger *bskLogger;   //!< BSK Logging
}IMUConfigData;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_imuProcessTelem(IMUConfigData *configData, int64_t moduleID);
    void CrossInit_imuProcessTelem(IMUConfigData *configData, int64_t moduleID);
    void Reset_imuProcessTelem(IMUConfigData *configData, uint64_t callTime, int64_t moduleId);
    void Update_imuProcessTelem(IMUConfigData *configData, uint64_t callTime,
        int64_t moduleID);
    
#ifdef __cplusplus
}
#endif


#endif
