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

#include <Eigen/Dense>
#include <vector>
#include <string>
#include "_GeneralModuleFiles/sys_model.h"
#include "simMessages/spicePlanetStateSimMsg.h"
#include "simMessages/scPlusStatesSimMsg.h"
#include "simMessages/powerStorageStatusSimMsg.h"
#include "simMessages/powerNodeUsageSimMsg.h"

#ifndef BASILISK_SIMPOWERSTORAGEBASE_H
#define BASILISK_SIMPOWERSTORAGEBASE_H

/*! \addtogroup SimModelGroup
 * @{
 */



//! @brief General power storage base class used to calculate net power in/out and stored power.


class PowerStorageBase: public SysModel  {
public:
    PowerStorageBase();
    ~PowerStorageBase();
    void SelfInit();
    void CrossInit();
    void Reset(uint64_t CurrentSimNanos);
    void addPowerNodeToModel(std::string tmpNodeMsgName);
    void UpdateState(uint64_t CurrentSimNanos);

protected:
    void writeMessages(uint64_t CurrentClock);
    bool readMessages();
    void integratePowerStatus(double currentTime);
    double sumAllInputs();
    virtual void evaluateBatteryModel(PowerStorageStatusSimMsg *msg, double time) = 0;
    virtual void customSelfInit();
    virtual void customCrossInit();
    virtual void customReset(uint64_t CurrentClock);
    virtual void customWriteMessages(uint64_t CurrentClock);
    virtual bool customReadMessages();

public:
    std::vector<std::string> nodePowerUseMsgNames;    //!< Vector of the spacecraft position/velocity message names
    std::string BatPowerOutMsgName; //!< Vector of message names to be written out by the battery
    double storedCharge; //!< [W-hr] Stored charge in Watt-hours.

private:
    std::vector<std::uint64_t> nodePowerUseMsgIds;
    std::vector<std::uint64_t> batPowerOutMsgId;
    PowerStorageStatusSimMsg storageStatusMsg;
    std::vector<PowerNodeUsageSimMsg> nodeWattMsgs;
    double previousTime; //! Previous time used for integration
    double currentPowerSum;

};


#endif //BASILISK_SIMPOWERSTORAGEBASE_H
