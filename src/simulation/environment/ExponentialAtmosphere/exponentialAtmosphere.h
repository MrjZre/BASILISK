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


#ifndef EXPONENTIAL_ATMOSPHERE_H
#define EXPONENTIAL_ATMOSPHERE_H

#include <Eigen/Dense>
#include <vector>
#include <string>
#include "../../_GeneralModuleFiles/sys_model.h"
#include "simMessages/spicePlanetStateSimMsg.h"
#include "simMessages/scPlusStatesSimMsg.h"
#include "simMessages/atmoPropsSimMsg.h"
#include "../_GeneralModuleFiles/atmosphereBase.h"

/*! \addtogroup SimModelGroup
 * @{
 */

/*! @brief Evaluate an exponential atmosphere model at a given height above a planetary surface.
 For more information on this module see this [PDF Documentation](Basilisk-atmosphere-20190221.pdf).

 */
class ExponentialAtmosphere:  public AtmosphereBase {
public:
    ExponentialAtmosphere();
    ~ExponentialAtmosphere();

private:
    void evaluateAtmosphereModel(AtmoPropsSimMsg *msg, double currentTime);


public:
    double baseDensity;             //!< [kg/m^3] Density at h=0
    double scaleHeight;             //!< [m] Exponential characteristic height
    double localTemp = 293.0;       //!< [K] Local atmospheric temperature; set to be constant.
};

/*! @} */

#endif /* EXPONENTIAL_ATMOSPHERE_H */
