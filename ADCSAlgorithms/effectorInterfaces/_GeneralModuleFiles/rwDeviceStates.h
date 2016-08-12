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

#ifndef _RW_DEVICE_STATES_H_
#define _RW_DEVICE_STATES_H_

#include <stdint.h>
#include "ADCSUtilities/ADCSDefinitions.h"
#include "../ADCSAlgorithms/effectorInterfaces/errorConversion/vehEffectorOut.h"

/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*! @brief Array with availability of RW */
typedef struct {
    int wheelAvailability[MAX_EFF_CNT];                //!< The current state of the wheel
}RWAvailabilityData;

/*! @} */

#endif
