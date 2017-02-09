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

#ifndef _THR_MOMENTUM_MANAGEMENT_H_
#define _THR_MOMENTUM_MANAGEMENT_H_

#include "messaging/static_messaging.h"
#include <stdint.h>
#include "../ADCSAlgorithms/vehicleConfigData/vehicleConfigData.h"
#include "fswMessages/vehicleConfigMessage.h"
#include "fswMessages/rwConfigMessage.h"
#include "fswMessages/cmdDelHMessage.h"
#include "../../../SimFswInterface/rwSpeedMessage.h"

/*! \addtogroup ADCSAlgGroup
 * @{
 */


/*! @brief Top level structure for the sub-module routines. */
typedef struct {
    /* declare module private variables */
    int initRequest;                                    /*!<        status flag of the momentum dumping management */
    double  Delta_H_B[3];                               /*!< [Nms]  net desired angular momentum change */
    RWConfigMessage rwConfigParams;                     /*!< [-] struct to store message containing RW config parameters in body B frame */

    /* declare module public variables */
    double hs_min;                                      /*!< [Nms]  minimum RW cluster momentum for dumping */
    
    /* declare module IO interfaces */
    char deltaHOutMsgName[MAX_STAT_MSG_LENGTH];         /*!< The name of the output message*/
    int32_t deltaHOutMsgID;                             /*!< ID for the outgoing message */
    char vehicleConfigDataInMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the Input message*/
    int32_t vehicleConfigDataInMsgID;                   /*!< [] ID for the incoming static vehicle data */
    char rwSpeedsInMsgName[MAX_STAT_MSG_LENGTH];        /*!< [] The name for the reaction wheel speeds message */
    int32_t rwSpeedsInMsgID;                            /*!< [] The ID for the reaction wheel speeds message*/
    char rwConfigDataInMsgName[MAX_STAT_MSG_LENGTH];    /*!< [-] The name of the RWA configuration message*/
    int32_t rwConfInMsgID;                              /*!< [-] ID for the incoming RWA configuration data*/


    CmdDelHMessage controlOut;                          /*!< [] Control output requests */

}thrMomentumManagementConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_thrMomentumManagement(thrMomentumManagementConfig *ConfigData, uint64_t moduleID);
    void CrossInit_thrMomentumManagement(thrMomentumManagementConfig *ConfigData, uint64_t moduleID);
    void Update_thrMomentumManagement(thrMomentumManagementConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void Reset_thrMomentumManagement(thrMomentumManagementConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    
#ifdef __cplusplus
}
#endif

/*! @} */

#endif
