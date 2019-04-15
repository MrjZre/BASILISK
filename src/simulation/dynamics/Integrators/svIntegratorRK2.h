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

#ifndef svIntegratorRK2_h
#define svIntegratorRK2_h

#include "../_GeneralModuleFiles/stateVecIntegrator.h"
#include "../_GeneralModuleFiles/dynParamManager.h"
#include <stdint.h>

/*! \addtogroup SimModelGroup Simulation C++ Modules
 * @{
 */

/*!
 @brief RK2 integrator. It only implements the method integrate() to advance one time step.

 The module
 [PDF Description](Basilisk-Integrators20170724.pdf)
 contains further information on this module's function,
 how to run it, as well as testing.

 */
class svIntegratorRK2 : public StateVecIntegrator
{
public:
    svIntegratorRK2(DynamicObject* dyn);
    virtual ~svIntegratorRK2();
    virtual void integrate(double currentTime, double timeStep);
    
};

/* @} */

#endif /* svIntegratorRK2_h */
