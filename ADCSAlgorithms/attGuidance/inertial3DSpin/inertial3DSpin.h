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

#ifndef _INERTIAL3D_SPIN_
#define _INERTIAL3D_SPIN_

#include "messaging/static_messaging.h"
#include <stdint.h>
#include "../_GeneralModuleFiles/attGuidOut.h"


/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*! @brief Top level structure for the sub-module routines. */
typedef struct {
    /* declare module private variables */
    double sigma_RN[3];                              /*!< [-] MRP from inertial frame N to initial ref frame R0 */
    double omega_RN_N[3];                            /*!< [r/s] angular velocity of R0 wrt N in N-frame components */
    uint64_t priorTime;                              /*!< [ns] last time the guidance module is called */
    double priorCmdSigma_RN[3];
    double dt;                                       /*!< [s] integration time-step */

    /* declare module IO interfaces */
    char outputDataName[MAX_STAT_MSG_LENGTH];        /*!< Name of the outgoing guidance reference message */
    int32_t outputMsgID;                             /*!< [-] ID for the outgoing guidance reference message */
    char inputRefName[MAX_STAT_MSG_LENGTH];          /*!< The name of the input guidance reference message */
    int32_t inputRefID;                              /*!< [-] ID for the incoming guidance reference message */
    attRefOut attRefOut;                             /*!< [-] structure for the output data */

}inertial3DSpinConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_inertial3DSpin(inertial3DSpinConfig *ConfigData, uint64_t moduleID);
    void CrossInit_inertial3DSpin(inertial3DSpinConfig *ConfigData, uint64_t moduleID);
    void Update_inertial3DSpin(inertial3DSpinConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void Reset_inertial3DSpin(inertial3DSpinConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void checkInputCommand(inertial3DSpinConfig *ConfigData, double cmdSigma_RN[3]);
    void writeOutputMessages(inertial3DSpinConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void computeTimeStep(inertial3DSpinConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void evaluateInertial3DSpinRef(inertial3DSpinConfig *ConfigData);
    void integrateInertialSpinRef(inertial3DSpinConfig *ConfigData);

#ifdef __cplusplus
}
#endif

/*! @} */

#endif
