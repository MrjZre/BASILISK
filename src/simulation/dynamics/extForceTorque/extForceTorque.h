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

#ifndef EXT_FORCE_TORQUE_H
#define EXT_FORCE_TORQUE_H

#include "architecture/messaging/messaging.h"
#include "architecture/_GeneralModuleFiles/sys_model.h"
#include "simulation/dynamics/_GeneralModuleFiles/dynamicEffector.h"

#include "architecture/msgPayloadDefC/CmdTorqueBodyMsgPayload.h"
#include "architecture/msgPayloadDefC/CmdForceBodyMsgPayload.h"
#include "architecture/msgPayloadDefC/CmdForceInertialMsgPayload.h"

#include "architecture/utilities/bskLogging.h"



/*! @brief external force and torque dynamic efector class */
class ExtForceTorque: public SysModel, public DynamicEffector{
public:
    ExtForceTorque();
    ~ExtForceTorque();

    void Reset(uint64_t CurrentSimNanos);
    void UpdateState(uint64_t CurrentSimNanos);         //!< class method
    void linkInStates(DynParamManager& statesIn, uint64_t spacecraftID);       //!< class method
    void writeOutputMessages(uint64_t currentClock);    //!< class method
    void readInputMessages();
    void computeForceTorque(double integTime, double timeStep, uint64_t spacecraftID);

private:
    CmdTorqueBodyMsgPayload incomingCmdTorqueBuffer;            //!< -- One-time allocation for savings
    CmdForceInertialMsgPayload incomingCmdForceInertialBuffer;  //!< -- One-time allocation for savings
    CmdForceBodyMsgPayload incomingCmdForceBodyBuffer;          //!< -- One-time allocation for savings


public:
    Eigen::Vector3d extForce_N;         //!< [N]  external force in inertial  frame components
    Eigen::Vector3d extForce_B;         //!< [N]  external force in body frame components
    Eigen::Vector3d extTorquePntB_B;    //!< [Nm] external torque in body frame components

    BSKLogger bskLogger;                      //!< -- BSK Logging
    ReadFunctor<CmdTorqueBodyMsgPayload> cmdTorqueInMsg;           //!< commanded torque input msg
    ReadFunctor<CmdForceBodyMsgPayload> cmdForceBodyInMsg;         //!< commanded force input msg in B frame
    ReadFunctor<CmdForceInertialMsgPayload>cmdForceInertialInMsg;  //!< commanded force input msg in N frame

};


#endif
