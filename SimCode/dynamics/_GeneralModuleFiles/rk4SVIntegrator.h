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

#ifndef rk4SVIntegrator_h
#define rk4SVIntegrator_h

#include "stateVecIntegrator.h"
#include "dynParamManager.h"
#include <stdint.h>

/*!
 @brief RK4 integrator. It only implements the method integrate() to advance one time step.
 */
class rk4SVIntegrator : public StateVecIntegrator
{
public:
    rk4SVIntegrator(DynamicObject* dyn);
    virtual ~rk4SVIntegrator();
    virtual void integrate(double currentTime, double timeStep);
    
    StateVector X2;       /* integration state space */
	StateVector k1;       /* intermediate RK results */
	StateVector k2;
	StateVector k3;
	StateVector k4;
};

#endif /* rk4SVIntegrator_h */
