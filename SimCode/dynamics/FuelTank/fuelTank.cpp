/*
 ISC License

 Copyright (c) 2016-2017, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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

#include "fuelTank.h"

/*! This is the constructor, setting variables to default values */
FuelTank::FuelTank() 
	:fuelSloshParticles()
{
	// - zero the contributions for mass props and mass rates
	this->effProps.mEff = 0.0;
    this->propMassInit = 0.0;
	this->effProps.IEffPntB_B.setZero();
	this->effProps.rEff_CB_B.setZero();
	this->effProps.rEffPrime_CB_B.setZero();
	this->effProps.IEffPrimePntB_B.setZero();

	// - Initialize the variables to working values
	this->r_TB_B.setZero();
	this->nameOfMassState = "fuelTankMass";

    return;
}

/*! This is the destructor, nothing to report here */
FuelTank::~FuelTank()
{
    return;
}

/*! This is a method to attach a fuel slosh particle to the tank */
void FuelTank::pushFuelSloshParticle(FuelSloshParticle particle)
{
    // - Add a fuel slosh particle to the vector of fuel slosh particles
	this->fuelSloshParticles.push_back(particle);

    return;
}

/*! Method for fuel tank to access the states that it needs, needs omega and fuel slosh particles */
void FuelTank::linkInStates(DynParamManager& statesIn)
{
    // - Grab access to fuel slosh particle states
	std::vector<FuelSloshParticle>::iterator intFSP;
	for (intFSP = this->fuelSloshParticles.begin(); intFSP < this->fuelSloshParticles.end(); intFSP++)
		intFSP->linkInStates(statesIn);

    // - Grab access to the hubs omega_BN_N
	this->omegaState = statesIn.getStateObject("hubOmega");

    return;
}

/*! Method for fuel tank to register states. The fuel tank has one state associated with it: mass, and it also has the
 responsibility to call register states for the fuel slosh particles */
void FuelTank::registerStates(DynParamManager& statesIn)
{
    // - Register the fuel slosh particle states
	std::vector<FuelSloshParticle>::iterator intFSP;
	for (intFSP = fuelSloshParticles.begin(); intFSP < fuelSloshParticles.end(); intFSP++)
		intFSP->registerStates(statesIn);

    // - Register the mass state associated with the tank
    Eigen::MatrixXd massMatrix(1,1);
	this->massState = statesIn.registerState(1, 1, this->nameOfMassState);
    massMatrix(0,0) = this->propMassInit;
    this->massState->setState(massMatrix);

    return;
}

/*! This method gives the fuel tank the ability to add its contributions the mass of the vehicle. It also has the
 responsibilty to add in the mass props of the fuel slosh particle(s) into the mass of the vehicle */
void FuelTank::updateEffectorMassProps(double integTime)
{
    // - Initialize certain variables to zero
    this->effProps.mEff = 0.0;
	this->effProps.IEffPntB_B = this->effProps.IEffPrimePntB_B = Eigen::Matrix3d::Zero();
	this->effProps.rEff_CB_B = effProps.rEffPrime_CB_B = Eigen::Vector3d::Zero();

	// - Incorporate the effects of all of the particles
    std::vector<FuelSloshParticle>::iterator intFSP;
	for (intFSP = this->fuelSloshParticles.begin(); intFSP < this->fuelSloshParticles.end(); intFSP++) {
		intFSP->updateEffectorMassProps(integTime);
		this->effProps.mEff += intFSP->effProps.mEff;
		this->effProps.IEffPntB_B += intFSP->effProps.IEffPntB_B;
		this->effProps.IEffPrimePntB_B += intFSP->effProps.IEffPrimePntB_B;
		this->effProps.rEff_CB_B += intFSP->effProps.mEff * intFSP->effProps.rEff_CB_B;
		this->effProps.rEffPrime_CB_B += intFSP->effProps.mEff * intFSP->effProps.rEffPrime_CB_B;
	}

	// - Add contributions of the mass of the tank
	double massLocal = this->massState->getState()(0, 0);
	this->effProps.mEff += massLocal;
    this->ITankPntT_B = (2.0 / 5.0 * massLocal * radiusTank * radiusTank) * Eigen::Matrix3d::Identity();
	this->effProps.IEffPntB_B += this->ITankPntT_B + massLocal * (r_TB_B.dot(r_TB_B)*Eigen::Matrix3d::Identity()
                                                                                         - r_TB_B * r_TB_B.transpose());
	this->effProps.rEff_CB_B += massLocal * r_TB_B;

    // - Scale the center of mass location by 1/m_tot
	this->effProps.rEff_CB_B /= effProps.mEff;
	this->effProps.rEffPrime_CB_B /= effProps.mEff;

    return;
}

/*! This method allows the fuel tank to add its contributions to the matrices for the back-sub method. In addition the
 fuel tank has the responsibility to add the contributions from the fuel slosh particles to the back-sub method */
void FuelTank::updateContributions(double integTime, Eigen::Matrix3d & matrixAcontr, Eigen::Matrix3d & matrixBcontr,
	Eigen::Matrix3d & matrixCcontr, Eigen::Matrix3d & matrixDcontr, Eigen::Vector3d & vecTranscontr,
	Eigen::Vector3d & vecRotcontr) {

    // - Zero some matrices
    matrixAcontr = matrixBcontr = matrixCcontr = matrixDcontr = Eigen::Matrix3d::Zero();
    vecTranscontr = vecRotcontr = Eigen::Vector3d::Zero();

    // - Get the contributions from the fuel slosh particles
    std::vector<FuelSloshParticle>::iterator intFSP;
	for (intFSP = fuelSloshParticles.begin(); intFSP < fuelSloshParticles.end(); intFSP++) {
		Eigen::Matrix3d Acontr, Bcontr, Ccontr, Dcontr;
		Eigen::Vector3d Transcontr, Rotcontr;
		intFSP->updateContributions(integTime, Acontr, Bcontr, Ccontr, Dcontr, Transcontr, Rotcontr);
		matrixAcontr += Acontr;
		matrixBcontr += Bcontr;
		matrixCcontr += Ccontr;
		matrixDcontr += Dcontr;
		vecTranscontr += Transcontr;
		vecRotcontr += Rotcontr;
	}
}

/*! This method allows the fuel tank to compute its derivative and also calls computeDeravites for the fuel slosh */
void FuelTank::computeDerivatives(double integTime)
{
    // - Call compute derivatives for all fuel slosh particles
	std::vector<FuelSloshParticle>::iterator intFSP;
	for (intFSP = fuelSloshParticles.begin(); intFSP < fuelSloshParticles.end(); intFSP++)
		intFSP->computeDerivatives(integTime);

	//! - Mass depletion (call thrusters attached to this tank to get their mDot)
	double fuelConsumption = 0.0;
	std::vector<DynamicEffector*>::iterator dynIt;
    for(dynIt = this->dynEffectors.begin(); dynIt != this->dynEffectors.end(); dynIt++)
    {
        (*dynIt)->computeStateContribution(integTime);
        fuelConsumption += (*dynIt)->stateDerivContribution(0);
    }
	Eigen::MatrixXd conv(1, 1);
	conv(0, 0) = -fuelConsumption;
	this->massState->setDerivative(conv);

    return;
}

/*! This method allows the fuel tank to contribute to the energy and momentum calculations and has the responsibiltiy of
 calling updateEnergyMomContributions for the fuel slosh particles */
void FuelTank::updateEnergyMomContributions(double integTime, Eigen::Vector3d & rotAngMomPntCContr_B,
                                            double & rotEnergyContr)
{
    // - call updateMassProps to get current mass props info
    this->updateEffectorMassProps(integTime);

    // - Get all of the fuel slosh particles contributions to energy and momentum
    std::vector<FuelSloshParticle>::iterator intFSP;
    for (intFSP = fuelSloshParticles.begin(); intFSP < fuelSloshParticles.end(); intFSP++)
    {
        Eigen::Vector3d rotAngMomPntCContrFSP_B;
        double rotEnergyContrFSP = 0.0;
        rotAngMomPntCContrFSP_B.setZero();
        intFSP->updateEnergyMomContributions(integTime, rotAngMomPntCContrFSP_B, rotEnergyContrFSP);
        rotAngMomPntCContr_B += rotAngMomPntCContrFSP_B;
        rotEnergyContr += rotEnergyContrFSP;
    }

    // - Get variables needed for energy momentum calcs
    Eigen::Vector3d omegaLocal_BN_B;
    omegaLocal_BN_B = omegaState->getState();
    Eigen::Vector3d rDot_TB_B;

    // - Find rotational angular momentum contribution from hub
    double massLocal = this->massState->getState()(0, 0);
    rDot_TB_B = omegaLocal_BN_B.cross(this->r_TB_B);
    rotAngMomPntCContr_B += this->ITankPntT_B*omegaLocal_BN_B + massLocal*this->r_TB_B.cross(rDot_TB_B);

    // - Find rotational energy contribution from the hub
    rotEnergyContr += 1.0/2.0*omegaLocal_BN_B.dot(this->ITankPntT_B*omegaLocal_BN_B) + 1.0/2.0*massLocal*
                                                                                               rDot_TB_B.dot(rDot_TB_B);
    
    return;
}
