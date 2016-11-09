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


#ifndef HUB_EFFECTOR_H
#define HUB_EFFECTOR_H

#include "../_GeneralModuleFiles/stateEffector.h"
#include "../_GeneralModuleFiles/stateData.h"
#include <Eigen/Dense>
#include "../SimCode/utilities/avsEigenMRP.h"

/*! @brief Abstract class that is used to implement an effector impacting a HUB body
           that does not itself maintain a state or represent a changing component of
           the body (for example: gravity, thrusters, solar radiation pressure, etc.)
 */
class HubEffector : public StateEffector {
public:
    HubEffector();
    ~HubEffector();
    void linkInStates(DynParamManager& statesIn);
    void registerStates(DynParamManager& states);
    void updateEffectorMassProps(double integTime);
    void computeDerivatives(double integTime);

public:
    double mHub;                         //!< [kg] mass of the hub
    Eigen::Vector3d rBcB_B;              //!< [m] vector from point B to CoM of hub in B frame components
    Eigen::Matrix3d IHubPntBc_B;         //!< [kg m^2] Inertia of hub about point Bc in B frame components
    Eigen::MatrixXd *m_SC;               //!< [kg] spacecrafts total mass
    Eigen::MatrixXd *ISCPntB_B;          //!< [kg m^2] Inertia of s/c about point B in B frame components
    Eigen::MatrixXd *c_B;                //!< [m] Vector from point B to CoM of s/c in B frame components
    Eigen::MatrixXd *cPrime_B;           //!< [m] Body time derivative of c_B
    Eigen::MatrixXd *ISCPntBPrime_B;     //!< [m] Body time derivative of ISCPntB_B
    Eigen::MatrixXd *g_N;                //!< [m/s^2] Gravitational acceleration in N frame components
    Eigen::Matrix3d matrixA;             //!< [-] Back-Substitution matrix A
    Eigen::Matrix3d matrixB;             //!< [-] Back-Substitution matrix B
    Eigen::Matrix3d matrixC;             //!< [-] Back-Substitution matrix C
    Eigen::Matrix3d matrixD;             //!< [-] Back-Substitution matrix D
    Eigen::Vector3d vecTrans;            //!< [-] Back-Substitution translation vector
    Eigen::Vector3d vecRot;              //!< [-] Back-Substitution rotation vector
    bool useTranslation;                 //!< [-] Whether the s/c has translational states
    bool useRotation;                    //!< [-] Whether the s/c has rotational states
    std::string nameOfHubPosition;       //!< [-] Identifier for hub position states
    std::string nameOfHubVelocity;       //!< [-] Identifier for hub velocity states
    std::string nameOfHubSigma;          //!< [-] Identifier for hub sigmaBN states
    std::string nameOfHubOmega;          //!< [-] Identifier for hub omegaBN_B states

private:
	StateData *posState;                 //!< [-] State data container for hub position
	StateData *velocityState;            //!< [-] State data container for hub velocity
    StateData *sigmaState;               //!< [-] State data container for hub sigmaBN
    StateData *omegaState;               //!< [-] State data container for hub omegaBN_B
};

#endif /* HUB_EFFECTOR_H */
