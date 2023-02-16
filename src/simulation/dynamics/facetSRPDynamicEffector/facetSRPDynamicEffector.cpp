/*
 ISC License

 Copyright (c) 2023, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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

#include "facetSRPDynamicEffector.h"

/*! The constructor initializes the member variables to zero. */
FacetSRPDynamicEffector::FacetSRPDynamicEffector()
{
}

/*! The destructor. */
FacetSRPDynamicEffector::~FacetSRPDynamicEffector()
{
}

/*! The reset member function. This method checks to ensure the input message is linked.
 @return void
 @param CurrentSimNanos [ns]  Time the method is called
*/
void FacetSRPDynamicEffector::Reset(uint64_t CurrentSimNanos)
{
}

/*! The SRP dynamic effector does not write any output messages.
 @return void
 @param CurrentClock [ns] Time the method is called
*/
void FacetSRPDynamicEffector::WriteOutputMessages(uint64_t CurrentClock)
{
}

/*! This member function populates the spacecraft geometry structure with user-input facet information.
 @return void
 @param area  [m^2] Facet area
 @param specCoeff  Facet spectral reflection optical coefficient
 @param diffCoeff  Facet diffuse reflection optical coefficient
 @param normal_B  Facet normal expressed in B frame components
 @param locationPntB_B  [m] Facet location wrt point B in B frame components
*/
void FacetSRPDynamicEffector::addFacet(double area, double specCoeff, double diffCoeff, Eigen::Vector3d normal_B, Eigen::Vector3d locationPntB_B)
{
}

/*! This method is used to link the faceted SRP effector to the hub attitude and position,
which are required for calculating SRP forces and torques.
 @return void
 @param states  Dynamic parameter states
*/
void FacetSRPDynamicEffector::linkInStates(DynParamManager& states)
{
}

/*! This method computes the body forces and torques for the SRP effector.
 @return void
 @param integTime  [s] Time the method is called
 @param timeStep  [s] Simulation time step
*/
void FacetSRPDynamicEffector::computeForceTorque(double integTime, double timeStep)
{
}

/*! This is the UpdateState() method
 @return void
 @param CurrentSimNanos [ns] Time the method is called
*/
void FacetSRPDynamicEffector::UpdateState(uint64_t CurrentSimNanos)
{
}