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

#ifndef _VEHICLE_CONFIG_DATA_H_
#define _VEHICLE_CONFIG_DATA_H_

#include <stdint.h>

/*! \addtogroup ADCSAlgGroup
 * @{
 */

#define MAX_EFF_CNT 36

/*! @brief Structure used to define a common structure for top level vehicle information*/
typedef struct {
    double BS[9];               /*!< -- DCM from vehicle structure frame S to ADCS body frame B (row major)*/
    uint32_t CurrentADCSState;  /*!< -- Current ADCS state for subsystem */
    double I[9];                /*!< kg m^2 Spacecraft Inertia */
}vehicleConfigData;


typedef struct {
    double Gs_S[3];             /*!< [-] Spin axis of the wheel in structure */
    double Js;                  /*!< [kgm2] Spin axis inertia of the wheel */
    double r_S[3];              /*!< [m] Location of the reaction wheel in structure*/
}RWConfigurationElement;

typedef struct {
    RWConfigurationElement reactionWheels[MAX_EFF_CNT];  /*!< [-] array of the reaction wheels */
}RWConstellation;

/*! @} */

#endif
