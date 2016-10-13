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


#include "hubEffector.h"

HubEffector::HubEffector()
{
    return;
}


HubEffector::~HubEffector()
{
    return;
}

void HubEffector::dynamicsSelfInit()
{

}

void HubEffector::dynamicsCrossInit()
{

}

void HubEffector::linkInStates(DynParamManager& statesIn)
{
    this->posState = statesIn.getStateObject("hubPosition");
    this->velocityState = statesIn.getStateObject("hubVelocity");
    this->sigmaState = statesIn.getStateObject("hubSigma");
    this->omegaState = statesIn.getStateObject("hubOmega");
    this->m_SC = statesIn.getPropertyReference("m_SC");
    this->c_B = statesIn.getPropertyReference("centerOfMassSC");
    this->ISCPntB_B = statesIn.getPropertyReference("inertiaSC");
    this->cPrime_B = statesIn.getPropertyReference("centerOfMassPrimeSC");
    this->ISCPntBPrime_B = statesIn.getPropertyReference("inertiaPrimeSC");
}

void HubEffector::registerStates(DynParamManager& states)
{
    states.registerState(3, 1, "hubPosition");
    states.registerState(3, 1, "hubVelocity");
    states.registerState(3, 1, "hubSigma");
    states.registerState(3, 1, "hubOmega");
}

//void updateContributions(double integTime)
//{
//}

void HubEffector::computeDerivatives(double integTime, Eigen::Matrix3d matrixA, Eigen::Matrix3d matrixB, Eigen::Matrix3d matrixC, Eigen::Matrix3d matrixD, Eigen::Vector3d vecTrans, Eigen::Vector3d vecRot)
{
    Eigen::Vector3d omegaBNDot_B;
    Eigen::Vector3d rBNDDotLocal_B;
    Eigen::Matrix3d intermediateMatrix;
    Eigen::Vector3d intermediateVector;
    Eigen::Vector3d omegaBNLocal;
    Eigen::Vector3d cPrimeLocal_B;
    Eigen::Vector3d cLocal_B;
    Eigen::Vector3d rBNDotLocal_N;
    Eigen::Matrix3d Bmat;
    Eigen::Vector3d sigmaBNLocal;
    Eigen::Vector3d sigmaBNDotLocal;
    Eigen::Matrix3d BN;
    double ms2;
    double s1s2;
    double s1s3;
    double s2s3;
    sigmaBNLocal = sigmaState->getState();
    omegaBNLocal = omegaState->getState();
    rBNDotLocal_N = velocityState->getState();
    cPrimeLocal_B = *cPrime_B;
    cLocal_B = *c_B;
    //! - Need to add hub to m_SC, c_B and ISCPntB_B
    *this->m_SC += this->mHub;
    *this->c_B += this->mHub*this->rBcB_B;
    *ISCPntB_B += this->IHubPntB_B;

    //! - Need to scale [A] [B] and vecTrans by m_SC
    matrixA = matrixA/this->m_SC->value();
    matrixA = matrixB/this->m_SC->value();
    vecTrans = vecTrans/this->m_SC->value();

    //! Need to make contributions to the matrices from the hub
    intermediateMatrix = intermediateMatrix.Identity();
    matrixA += intermediateMatrix;
    //! make c_B skew symmetric matrix
    intermediateMatrix <<  0 , -(*c_B)(2,0),
    (*c_B)(1,0), (*c_B)(2,0), 0, -(*c_B)(0,0), -(*c_B)(1,0), (*c_B)(0,0), 0;
    matrixB -= intermediateMatrix;
    matrixC += this->m_SC->value()*intermediateMatrix;
    matrixD += *ISCPntB_B;
    vecTrans += -2*omegaBNLocal.cross(cPrimeLocal_B) -omegaBNLocal.cross(omegaBNLocal.cross(cLocal_B));
    intermediateVector = *ISCPntB_B*omegaBNLocal;
    vecRot += -omegaBNLocal.cross(intermediateVector) - *ISCPntBPrime_B*omegaBNLocal;

    if (this->useRotation) {
        //! Set kinematic derivative
        ms2  = 1 - sigmaBNLocal.squaredNorm();
        s1s2 = sigmaBNLocal(0)*sigmaBNLocal(1);
        s1s3 = sigmaBNLocal(0)*sigmaBNLocal(2);
        s2s3 = sigmaBNLocal(1)*sigmaBNLocal(2);

        Bmat(0,0) = ms2 + 2*sigmaBNLocal(0)*sigmaBNLocal(0);
        Bmat(0,1) = 2*(s1s2 - sigmaBNLocal(2));
        Bmat(0,2) = 2*(s1s3 + sigmaBNLocal(1));
        Bmat(1,0) = 2*(s1s2 + sigmaBNLocal(2));
        Bmat(1,1) = ms2 + 2*sigmaBNLocal(1)*sigmaBNLocal(1);
        Bmat(1,2) = 2*(s2s3 - sigmaBNLocal(0));
        Bmat(2,0) = 2*(s1s3 - sigmaBNLocal(1));
        Bmat(2,1) = 2*(s2s3 + sigmaBNLocal(0));
        Bmat(2,2) = ms2 + 2*sigmaBNLocal(2)*sigmaBNLocal(2);
        sigmaBNDotLocal = 1/4*Bmat*omegaBNLocal;
        sigmaState->setDerivative(sigmaBNDotLocal);

        if (useTranslation) {
            intermediateVector = vecRot - matrixC*matrixA.inverse()*vecTrans;
            intermediateMatrix = matrixD - matrixC*matrixA.inverse()*matrixB;
            omegaBNDot_B = intermediateMatrix.inverse()*intermediateVector;
            omegaState->setDerivative(omegaBNDot_B);
            rBNDDotLocal_B = matrixA.inverse()*(vecTrans - matrixB*omegaBNDot_B);
            //! - Map rBNDDotLocal_B to rBNDotLocal_N
            velocityState->setDerivative(rBNDDotLocal_B);
        }
        omegaBNDot_B = matrixD.inverse()*vecRot;
        omegaState->setDerivative(omegaBNDot_B);
    }

    if (useTranslation) {
        //! - Set kinematic derivative
        posState->setDerivative(rBNDotLocal_N);
        if (useRotation==false) {
            rBNDDotLocal_B = matrixA.inverse()*(vecTrans);

        }

    }
}

void updateEffectorMassProps(double integTime){}
void updateEffectorMassPropRates(double integTime){}
