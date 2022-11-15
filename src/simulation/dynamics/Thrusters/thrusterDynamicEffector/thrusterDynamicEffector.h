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


#ifndef THRUSTER_DYNAMIC_EFFECTOR_H
#define THRUSTER_DYNAMIC_EFFECTOR_H

#include "simulation/dynamics/_GeneralModuleFiles/dynamicEffector.h"
#include "simulation/dynamics/_GeneralModuleFiles/stateData.h"
#include "simulation/dynamics/_GeneralModuleFiles/THRTimePair.h"
#include "simulation/dynamics/_GeneralModuleFiles/THRSimConfig.h"
#include "simulation/dynamics/_GeneralModuleFiles/THROperation.h"
#include "architecture/_GeneralModuleFiles/sys_model.h"

#include "architecture/msgPayloadDefCpp/THROutputMsgPayload.h"
#include "architecture/msgPayloadDefC/THRArrayOnTimeCmdMsgPayload.h"
#include "architecture/msgPayloadDefC/SCStatesMsgPayload.h"
#include "architecture/messaging/messaging.h"

#include "architecture/utilities/bskLogging.h"
#include <Eigen/Dense>
#include <vector>

 /*! attached body to hub information structure*/
struct BodyToHubInfo {
    Eigen::Vector3d r_FB_B;
    Eigen::Vector3d omega_FB_B;
    Eigen::Matrix3d dcm_BF;
};


/*! @brief thruster dynamic effector class */
class ThrusterDynamicEffector: public SysModel, public DynamicEffector {
public:
    ThrusterDynamicEffector();
    ~ThrusterDynamicEffector();
    void linkInStates(DynParamManager& states);
    void computeForceTorque(double integTime, double timeStep);
    void computeStateContribution(double integTime);
    void Reset(uint64_t CurrentSimNanos);
    //! Add a new thruster to the thruster set
    void addThruster(THRSimConfig* newThruster);
    void addThruster(THRSimConfig* newThruster, Message<SCStatesMsgPayload>* bodyStateMsg); //!< -- (overloaded) Add a new thruster to the thruster set connect to a body different than the hub
    void UpdateState(uint64_t CurrentSimNanos);
    void writeOutputMessages(uint64_t CurrentClock);
    bool ReadInputs();
    void ConfigureThrustRequests(double currentTime);
    void ComputeThrusterFire(THRSimConfig *CurrentThruster, double currentTime);
    void ComputeThrusterShut(THRSimConfig *CurrentThruster, double currentTime);
    void UpdateThrusterProperties();
    

public:
    ReadFunctor<THRArrayOnTimeCmdMsgPayload> cmdsInMsg;  //!< -- input message with thruster commands
    std::vector<Message<THROutputMsgPayload>*> thrusterOutMsgs;  //!< -- output message vector for thruster data

    int stepsInRamp;                               //!< class variable
    std::vector<THRSimConfig> thrusterData; //!< -- Thruster information
    std::vector<double> NewThrustCmds;             //!< -- Incoming thrust commands
    double mDotTotal;                              //!< kg/s Current mass flow rate of thrusters
    double prevFireTime;                           //!< s  Previous thruster firing time
	double thrFactorToTime(THRSimConfig *thrData,
		std::vector<THRTimePair> *thrRamp);
	StateData *hubSigma;                           //!< class variable
    StateData *hubOmega;                           //!< class varaible
    StateData* hubPosition;        //!< class variable
    StateData* hubVelocity;        //!< class variable
    BSKLogger bskLogger;                      //!< -- BSK Logging

private:
    std::vector<THROutputMsgPayload> thrusterOutBuffer;//!< -- Message buffer for thruster data
    THRArrayOnTimeCmdMsgPayload incomingCmdBuffer;     //!< -- One-time allocation for savings

    std::vector<ReadFunctor<SCStatesMsgPayload>> attachedBodyInMsgs;       //!< (optional) vector of body states message where the thrusters attach to
    SCStatesMsgPayload attachedBodyBuffer;
    std::vector<BodyToHubInfo> bodyToHubInfo;

    uint64_t prevCommandTime;                       //!< -- Time for previous valid thruster firing

};


#endif /* THRUSTER_DYNAMIC_EFFECTOR_H */
