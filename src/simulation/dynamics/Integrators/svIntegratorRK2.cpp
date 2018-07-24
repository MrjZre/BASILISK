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


#include "svIntegratorRK2.h"
#include "../_GeneralModuleFiles/dynamicObject.h"
#include <stdio.h>

svIntegratorRK2::svIntegratorRK2(DynamicObject* dyn) : StateVecIntegrator(dyn)
{
    
    return;
}

svIntegratorRK2::~svIntegratorRK2()
{
    return;
}

/*<!
 Implements a 2nd order Runge Kutta integration method called Heun's method
 see [Wiki Page on Heun's Method](https://en.wikipedia.org/wiki/Heun%27s_method#Runge.E2.80.93Kutta_method)
 */
void svIntegratorRK2::integrate(double currentTime, double timeStep)
{
	StateVector stateOut;
	StateVector stateInit;
	std::map<std::string, StateData>::iterator it;
	std::map<std::string, StateData>::iterator itOut;
	std::map<std::string, StateData>::iterator itInit;
	stateOut = dynPtr->dynManager.getStateVector();
	stateInit = dynPtr->dynManager.getStateVector();
    dynPtr->equationsOfMotion(currentTime);
    for (it = dynPtr->dynManager.stateContainer.stateMap.begin(), itOut = stateOut.stateMap.begin(), itInit = stateInit.stateMap.begin(); it != dynPtr->dynManager.stateContainer.stateMap.end(); it++, itOut++, itInit++)
    {
        itOut->second.setDerivative(it->second.getStateDeriv());
        itOut->second.propagateState(timeStep / 2.0);
        it->second.state = itInit->second.state + timeStep*it->second.stateDeriv;
    }

    dynPtr->equationsOfMotion(currentTime + timeStep);
    for (it = dynPtr->dynManager.stateContainer.stateMap.begin(), itOut = stateOut.stateMap.begin(), itInit = stateInit.stateMap.begin(); it != dynPtr->dynManager.stateContainer.stateMap.end(); it++, itOut++, itInit++)
    {
        itOut->second.setDerivative(it->second.getStateDeriv());
        itOut->second.propagateState(timeStep / 2.0);
    }

	dynPtr->dynManager.updateStateVector(stateOut);	

    return;
}


