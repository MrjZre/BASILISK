/*
Copyright (c) 2016, Autonomous Vehicle Systems Lab, Univeristy of Colorado at Boulder

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

#ifndef _CELESTIAL_BODY_POINT_H_
#define _CELESTIAL_BODY_POINT_H_

#include "messaging/static_messaging.h"
#include "attGuidance/_GeneralModuleFiles/attGuidOut.h"
#include <stdint.h>

/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*! @brief Top level structure for the nominal delta-V guidance*/
typedef struct {
    /* Declare module private variables */
    double singularityThresh;                       /*!< (r) Threshold for when to fix constraint axis*/
    uint32_t prevAvail;                             /*!< (-) Flag indicating whether the previous constraint axis is populated*/
	double prevConstraintAxis[3];                   /*!< (-) Previous setting for constraint axis*/
    double prevConstraintAxisDot[3];                /*!< (-) First time-derivative of previous constraint axis */
    double prevConstraintAxisDoubleDot[3];          /*!< (-) Secod time-derivative of previous constraint axis */
    
    /* Declare module IO interfaces */
    char outputDataName[MAX_STAT_MSG_LENGTH];       /*!< The name of the output message*/
    char inputNavDataName[MAX_STAT_MSG_LENGTH];     /*<! The name of the incoming attitude command*/
    char inputCelMessName[MAX_STAT_MSG_LENGTH];     /*<! The name of the celestial body message*/
    char inputSecMessName[MAX_STAT_MSG_LENGTH];     /*<! The name of the secondary body to constrain point*/
    int32_t outputMsgID;                            /*!< (-) ID for the outgoing body estimate message*/
    int32_t inputNavID;                             /*!< (-) ID for the incoming IMU data message*/
    int32_t inputCelID;                             /*!< (-) ID for the incoming mass properties message*/
    int32_t inputSecID;                             /*!< (-) ID for the secondary constraint message*/
    
    /* Output attitude reference data to send */
    attRefOut attRefOut;
}celestialTwoBodyPointConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_celestialTwoBodyPoint(celestialTwoBodyPointConfig *ConfigData, uint64_t moduleID);
    void CrossInit_celestialTwoBodyPoint(celestialTwoBodyPointConfig *ConfigData, uint64_t moduleID);
    void Update_celestialTwoBodyPoint(celestialTwoBodyPointConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void Reset_celestialTwoBodyPoint(celestialTwoBodyPointConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void computecelestialTwoBodyPoint(celestialTwoBodyPointConfig *ConfigData,
                                      double R_P1[3],
                                      double v_P1[3],
                                      double a_P1[3],
                                      double R_P2[3],
                                      double v_P2[3],
                                      double a_P2[3],
                                      uint64_t callTime,
                                      double sigma_RN[3],
                                      double omega_RN_N[3],
                                      double domega_RN_N[3]);
    
#ifdef __cplusplus
}
#endif

/*! @} */

#endif
