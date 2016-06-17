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
#include "sensors/sun_sensor/coarse_sun_sensor.h"
#include "architecture/messaging/system_messaging.h"
#include "utilities/rigidBodyKinematics.h"
#include "utilities/linearAlgebra.h"
#include <math.h>
#include <iostream>
#include <cstring>
#include <random>

CoarseSunSensor::CoarseSunSensor()
{
    CallCounts = 0;
    this->MessagesLinked = false;
    this->InputSunID = -1;
    this->InputStateID = -1;
    this->InputStateMsg = "inertial_state_output";
    this->InputSunMsg = "sun_display_frame_data";
    this->OutputDataMsg = "coarse_sun_data";
    this->isOutputtingMeasured = true;
    this->SenBias = 0.0;
    this->SenNoiseStd = 0.0;
    this->faultState = MAX_CSSFAULT;
    this->stuckPercent = 0.0;
    v3SetZero(this->nHatStr);
    v3SetZero(this->horizonPlane);
    this->directValue = 0.0;
    this->albedoValue = 0.0;
    this->scaleFactor = 1.0;
    this->KellyFactor = 0.0; ///- Removes kelly curve
    this->sensedValue = 0.0;
    this->fov           = 1.0471975512; /// 60*degrees2rad
    this->maxVoltage    = 0.0;
    this->phi           = 0.785398163397;
    this->theta         = 0.0;
    v3SetZero(this->B2P321Angles);
    v3SetZero(this->r_B);
    this->setStructureToPlatformDCM(B2P321Angles[0], B2P321Angles[1], B2P321Angles[2]);
    this->setUnitDirectionVectorWithPerturbation(0, 0);
    this->OutputBufferCount = 2;
    
    return;
}

/*
 * Purpose: Set the unit direction vector (in the body frame) with applied azimuth and elevation angle perturbations.
 *
 *   @param[in] cssPhiPerturb   (radians) css elevation angle, measured positive toward the body z axis from the x-y plane
 *   @param[in] cssThetaPerturb (radians) css azimuth angle, measured positive from the body +x axis around the +z axis
 */
void CoarseSunSensor::setUnitDirectionVectorWithPerturbation(double cssThetaPerturb, double cssPhiPerturb)
{
    double tempPhi = this->phi + cssPhiPerturb;
    double tempTheta = this->theta + cssThetaPerturb;
    
    //    // Wrap azimuth angle to interval [0,360)
    //    if (tempTheta >= M_2_PI | tempTheta < 0) {
    //        tempTheta = this->wrapTo2PI(tempTheta);
    //    }
    //    // Wrap elevation angle to interval [0,90]
    //    if (tempPhi > M_PI/2 | tempPhi < 0) {
    //        tempPhi =  this->wrapToHalfPI(tempPhi);
    //    }
    
    // Rotation from individual photo diode sensor frame (S) to css platform frame (P)
    double sensorV3_P[3] = {0,0,0}; // sensor diode normal in platform frame
    //double PS[3][3];              // rotation matrix sensor to platform frame
    double BP[3][3];                // rotation matrix platform to body frame
    
    // azimuth and elevation rotations of vec transpose(1,0,0) where vec is the unit normal
    // of the photo diode
    sensorV3_P[0] = cos(tempPhi) * cos(tempTheta);
    sensorV3_P[1] = cos(tempPhi) * sin(tempTheta);
    sensorV3_P[2] = sin(tempPhi);
    
    // Rotation from P frame to structure frame (B)
    m33Transpose(this->PB, BP);
    m33MultV3(BP, sensorV3_P, this->nHatStr);
}

/*
 * Purpose: Set the direction cosine matrix body to css platform tranformation with 3-2-1 angle set.
 *
 *   @param[in] yaw   (radians) third axis rotation about body +z
 *   @param[in] pitch (radians) second axis rotation about interim frame +y
 *   @param[in] roll  (radians) first axis rotation about platform frame +x
 */
void CoarseSunSensor::setStructureToPlatformDCM(double yaw, double pitch, double roll)
{
    double q[3] = {yaw, pitch, roll};
    Euler3212C(q, this->PB);
}


CoarseSunSensor::~CoarseSunSensor()
{
    return;
}

void CoarseSunSensor::SelfInit()
{
    std::normal_distribution<double>::param_type
    UpdatePair(this->SenBias, this->SenNoiseStd);
    rgen.seed(RNGSeed);
    rnum.param(UpdatePair);
    OutputDataID = SystemMessaging::GetInstance()->
        CreateNewMessage(OutputDataMsg, sizeof(CSSOutputData),
        OutputBufferCount, "CSSOutputData", moduleID);
}

void CoarseSunSensor::CrossInit()
{
    LinkMessages();
}

bool CoarseSunSensor::spacecraftIlluminated()
{
    return(true); /// Sun is always shining baby.  Fix this...
}

bool CoarseSunSensor::LinkMessages()
{
    InputSunID = SystemMessaging::GetInstance()->subscribeToMessage(InputSunMsg,
        sizeof(SpicePlanetState), moduleID);
    InputStateID = SystemMessaging::GetInstance()->subscribeToMessage(InputStateMsg,
        sizeof(OutputStateData), moduleID);
        
    if(InputSunID >= 0 && InputStateID >= 0)
    {
        return(true);
    }
    else
    {
        std::cerr << "WARNING: Failed to link a sun sensor input message: ";
        std::cerr << std::endl << "Sun: "<<InputSunID;
        std::cerr << std::endl << "Sun: "<<InputStateID;
    }
    return(false);
}

void CoarseSunSensor::readInputMessages()
{
    SingleMessageHeader LocalHeader;
    
    memset(&this->SunData, 0x0, sizeof(SpicePlanetState));
    memset(&this->StateCurrent, 0x0, sizeof(OutputStateData));
    if(InputSunID >= 0)
    {
        SystemMessaging::GetInstance()->ReadMessage(InputSunID, &LocalHeader,
                                                    sizeof(SpicePlanetState), reinterpret_cast<uint8_t*> (&this->SunData), moduleID);
    }
    if(InputStateID >= 0)
    {
        SystemMessaging::GetInstance()->ReadMessage(InputStateID, &LocalHeader,
                                                    sizeof(OutputStateData), reinterpret_cast<uint8_t*> (&this->StateCurrent), moduleID);
    }
}

void CoarseSunSensor::computeSunData()
{
    double Sc2Sun_Inrtl[3];
    double sHatSunBdy[3];
    double T_Irtl2Bdy[3][3];
    
    v3Scale(-1.0, this->StateCurrent.r_N, Sc2Sun_Inrtl);
    v3Add(Sc2Sun_Inrtl, this->SunData.PositionVector, Sc2Sun_Inrtl);
    v3Normalize(Sc2Sun_Inrtl, Sc2Sun_Inrtl);
    MRP2C(this->StateCurrent.sigma, T_Irtl2Bdy);
    m33MultV3(T_Irtl2Bdy, Sc2Sun_Inrtl, sHatSunBdy);
    m33MultV3(this->StateCurrent.T_str2Bdy, sHatSunBdy, this->sHatStr);
}

void CoarseSunSensor::computeTruthOutput()
{
    double temp1 = v3Dot(this->nHatStr, this->sHatStr);
    this->directValue = 0.0;
    if(temp1 >= cos(this->fov))
    {
       this->directValue = temp1;
    }
    albedoValue = 0.0; ///-placeholder
    this->trueValue = this->directValue + this->albedoValue;
}

void CoarseSunSensor::applySensorErrors()
{
    double CurrentError = rnum(rgen);
    double KellyFit = 1.0 - exp(-this->directValue * this->directValue / this->KellyFactor);
    this->sensedValue = (this->trueValue)*KellyFit + CurrentError;
}
void CoarseSunSensor::scaleActualOutput()
{
    this->ScaledValue = this->outputValue * this->scaleFactor;
}

void CoarseSunSensor::writeOutputMessages(uint64_t Clock)
{
    CSSOutputData LocalMessage;
    memset(&LocalMessage, 0x0, sizeof(CSSOutputData));
    LocalMessage.OutputData = this->ScaledValue;
    SystemMessaging::GetInstance()->WriteMessage(OutputDataID, Clock, 
                                                 sizeof(CSSOutputData), reinterpret_cast<uint8_t *> (&LocalMessage), moduleID);
}

void CoarseSunSensor::UpdateState(uint64_t CurrentSimNanos)
{
    readInputMessages();
    computeSunData();
    computeTruthOutput();
    if (this->isOutputtingMeasured)
    {
        applySensorErrors();
        this->outputValue = this->sensedValue;
    } else {
        this->outputValue = this->trueValue;
    }
    // Output value needs to be scaled whether errors are embedded or not
    scaleActualOutput();
    writeOutputMessages(CurrentSimNanos);
}
