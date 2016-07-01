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
#include "sensors/star_tracker/star_tracker.h"
#include "architecture/messaging/system_messaging.h"
#include "utilities/RigidBodyKinematics.h"
#include "../ADCSAlgorithms/ADCSUtilities/ADCSAlgorithmMacros.h"
#include <iostream>

StarTracker::StarTracker()
{
    CallCounts = 0;
    this->messagesLinked = false;
    this->inputTimeID = -1;
    this->inputStateID = -1;
    this->inputTimeMessage = "spice_time_output_data";
    this->inputStateMessage = "inertial_state_output";
    this->outputStateMessage = "star_tracker_state";
    this->OutputBufferCount = 2;
    m33SetIdentity(RECAST3X3 this->T_CaseStr);
    return;
}

StarTracker::~StarTracker()
{
    return;
}

bool StarTracker::LinkMessages()
{
    inputTimeID = SystemMessaging::GetInstance()->subscribeToMessage(
        inputTimeMessage, sizeof(SpiceTimeOutput), moduleID);
    inputStateID = SystemMessaging::GetInstance()->subscribeToMessage(
        inputStateMessage, sizeof(OutputStateData), moduleID);
    
    
    return(inputTimeID >=0 && inputStateID >= 0);
}

void StarTracker::SelfInit()
{
    //! Begin method steps
    uint64_t numStates = 3;
    outputStateID = SystemMessaging::GetInstance()->
        CreateNewMessage(outputStateMessage, sizeof(StarTrackerHWOutput),
        OutputBufferCount, "StarTrackerHWOutput", moduleID);
    
    AMatrix.clear();
    AMatrix.insert(AMatrix.begin(), numStates*numStates, 0.0);
    mSetIdentity(AMatrix.data(), numStates, numStates);
    for(uint32_t i=0; i<3; i++)
    {
		AMatrix.data()[i * 3 + i] = 1.0;
    }
    //! - Alert the user if the noise matrix was not the right size.  That'd be bad.
    if(PMatrix.size() != numStates*numStates)
    {
        std::cerr << __FILE__ <<": Your process noise matrix (PMatrix) is not 18*18.";
        std::cerr << "  You should fix that.  Popping zeros onto end"<<std::endl;
        PMatrix.insert(PMatrix.begin()+PMatrix.size(), numStates*numStates - PMatrix.size(),
                       0.0);
    }
    errorModel.setNoiseMatrix(PMatrix);
    errorModel.setRNGSeed(RNGSeed);
    errorModel.setUpperBounds(walkBounds);
}

void StarTracker::CrossInit()
{
    messagesLinked = LinkMessages();
}

void StarTracker::readInputMessages()
{
    SingleMessageHeader localHeader;
    
    if(!this->messagesLinked)
    {
        this->messagesLinked = LinkMessages();
    }
    
    memset(&this->timeState, 0x0, sizeof(SpiceTimeOutput));
    memset(&this->scState, 0x0, sizeof(OutputStateData));
    if(inputStateID >= 0)
    {
        SystemMessaging::GetInstance()->ReadMessage(inputStateID, &localHeader,
                                                    sizeof(OutputStateData), reinterpret_cast<uint8_t*>(&scState), moduleID);
    }
    if(inputTimeID >= 0)
    {
        SystemMessaging::GetInstance()->ReadMessage(inputTimeID, &localHeader,
                                                    sizeof(SpiceTimeOutput), reinterpret_cast<uint8_t*>(&timeState), moduleID);
        this->envTimeClock = localHeader.WriteClockNanos;
    }
}

void StarTracker::computeSensorErrors()
{
    this->errorModel.setPropMatrix(AMatrix);
    this->errorModel.computeNextState();
    this->navErrors = this->errorModel.getCurrentState();
}

void StarTracker::applySensorErrors()
{
    double sigmaSensed[3];
    PRV2MRP(&(navErrors.data()[0]), this->mrpErrors);
    addMRP(scState.sigma, this->mrpErrors, sigmaSensed);
    computeQuaternion(sigmaSensed, &this->sensedValues);
    this->sensedValues.timeTag = this->sensorTimeTag;
}

void StarTracker::computeQuaternion(double *sigma, StarTrackerHWOutput *sensorValues)
{
    double T_BdyInrtl[3][3];
    double T_StrInrtl[3][3];
    double T_CaseInrtl[3][3];
    MRP2C(sigma, T_BdyInrtl);
    m33tMultM33(scState.T_str2Bdy, T_BdyInrtl, T_StrInrtl);
    m33MultM33(RECAST3X3 T_CaseStr, T_StrInrtl, T_CaseInrtl);
    C2EP(T_CaseInrtl, sensorValues->qInrtl2Case);
}

void StarTracker::computeSensorTimeTag(uint64_t CurrentSimNanos)
{
    this->sensorTimeTag = this->timeState.J2000Current;
    this->sensorTimeTag += (CurrentSimNanos - this->envTimeClock)*1.0E-9;
}

void StarTracker::computeTrueOutput()
{
    this->trueValues.timeTag = this->sensorTimeTag;
    computeQuaternion(this->scState.sigma, &this->trueValues);
}


void StarTracker::writeOutputMessages(uint64_t CurrentSimNanos)
{
    SystemMessaging::GetInstance()->WriteMessage(outputStateID, CurrentSimNanos,
                                                 sizeof(StarTrackerHWOutput), reinterpret_cast<uint8_t *>(&this->sensedValues), moduleID);
}

void StarTracker::UpdateState(uint64_t CurrentSimNanos)
{
    readInputMessages();
    computeSensorTimeTag(CurrentSimNanos);
    computeSensorErrors();
    computeTrueOutput();
    applySensorErrors();
    writeOutputMessages(CurrentSimNanos);
}
