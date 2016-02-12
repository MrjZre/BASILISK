
#ifndef _orbitAxis_SPIN_
#define _orbitAxis_SPIN_

#include "messaging/static_messaging.h"
#include <stdint.h>
#include "../_GeneralModuleFiles/attGuidOut.h"


/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*! @brief Top level structure for the sub-module routines. */



typedef struct {
    /* declare module private variables */
    int     o_spin;                                  /*!< [0,1,2]   Orbit axis around which to spin */
    double  omega_spin;                              /*!< [rad/sec] Desired spinning rate */
    double  phi_spin;                                /*!< [rad]     Current  spin angle */
    double  dt;                                      /*!< [rad]     Module update time */
    int     integrateFlag;
    int     b_spin;                                  /*!< [0,1,2]   Body axis around which to spin */
    
    /* declare module IO interfaces */
    char outputDataName[MAX_STAT_MSG_LENGTH];       /*!<        The name of the output message*/
    int32_t outputMsgID;                            /*!< (-)    ID for the outgoing message */
    char inputRefName[MAX_STAT_MSG_LENGTH];         /*!< The name of the guidance reference Input message */
    int32_t inputRefID;                             /*!< ID for the incoming guidance reference message */
    char inputNavName[MAX_STAT_MSG_LENGTH];         /*!< The name of the navigation Input message */
    int32_t inputNavID;                             /*!< ID for the incoming navigation message */
    
    /*  copy of the output message */
    attRefOut attRefOut;
    
}orbitAxisSpinConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_orbitAxisSpin(orbitAxisSpinConfig *ConfigData, uint64_t moduleID);
    void CrossInit_orbitAxisSpin(orbitAxisSpinConfig *ConfigData, uint64_t moduleID);
    void Update_orbitAxisSpin(orbitAxisSpinConfig *ConfigData, uint64_t callTime, uint64_t moduleID);
    void Reset_orbitAxisSpin(orbitAxisSpinConfig *ConfigData);
    void computeOrbitAxisSpinReference(orbitAxisSpinConfig *ConfigData,
                                       double sigma_R0N[3],
                                       double omega_R0N_N[3],
                                       double domega_R0N_N[3],
                                       double dt,
                                       double sigma_RN[3],
                                       double omega_RN_N[3],
                                       double domega_RN_N[3]);
    
    double computeInitialSpinAngle(orbitAxisSpinConfig *ConfigData,
                                   double sigma_R0N[3],
                                   double sigma_BN[3]);
    
#ifdef __cplusplus
}
#endif

/*! @} */

#endif
