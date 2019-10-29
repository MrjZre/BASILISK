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


#ifndef VIZ_INTERFACE_H
#define VIZ_INTERFACE_H

#include "vizProtobuffer/vizMessage.pb.h"
#include <vector>
#include <fstream>
#include <map>
#include <zmq.h>

#include "_GeneralModuleFiles/sys_model.h"
#include "architecture/messaging/system_messaging.h"
#include "simFswInterfaceMessages/stSensorIntMsg.h"
#include "simFswInterfaceMessages/cameraConfigMsg.h"
#include "simFswInterfaceMessages/cameraImageMsg.h"
#include "simMessages/spicePlanetStateSimMsg.h"
#include "simMessages/rwConfigLogSimMsg.h"
#include "simMessages/scPlusStatesSimMsg.h"
#include "simFswInterfaceMessages/cssArraySensorIntMsg.h"
#include "simMessages/thrOutputSimMsg.h"
#include "simFswInterfaceMessages/rwSpeedIntMsg.h"
#include "../fswAlgorithms/fswMessages/cssConfigFswMsg.h"
#include "../fswAlgorithms/fswMessages/thrArrayConfigFswMsg.h"

#define VIZ_MAX_SIZE 100000

typedef struct {
    int64_t msgID;        //!< [-] message ID associated with source
    uint64_t lastTimeTag; //!< [ns] The previous read time-tag for msg
    bool dataFresh;       //!< [-] Flag indicating that new data has been read
}MsgCurrStatus;

typedef struct {
    std::string thrTag;   //!< [-] ModelTag associated with the thruster model
    uint32_t    thrCount; //!< [-] Number of thrusters used in this thruster model
}ThrClusterMap;

typedef struct {
    uint32_t byte_count;
    uint8_t buffer[VIZ_MAX_SIZE];
}VizMsg;

typedef struct {
    std::string scName;
    std::string cssDataInMsgName;             //! [-] Name of the incoming css data
    std::string cssConfInMsgName;             //! [-] Name of the incoming css constellation data
    std::string cameraConfInMsgName;             //! [-] Name of the incoming camera data
    std::string scPlusInMsgName;              //! [-] Name of the incoming SCPlus data
    std::vector <std::string> rwInMsgName;    //! [-] Name of the incoming rw data
    std::vector <ThrClusterMap> thrMsgData;     //! [-] Name of the incoming thruster data
    std::string starTrackerInMsgName;         //! [-] Name of the incoming Star Tracker data
    std::string opnavImageOutMsgName;           //! The name of the Image output message*/
    std::vector<MsgCurrStatus> rwInMsgID;                        //! [-] ID of the incoming rw data
    std::vector<MsgCurrStatus> thrMsgID;                  //! [-] ID of the incoming thruster data
    MsgCurrStatus starTrackerInMsgID;               //! [-] ID of the incoming Star Tracker data
    MsgCurrStatus scPlusInMsgID;                    //! [-] ID of the incoming SCPlus data
    MsgCurrStatus cssDataInMsgId;                   //! [-] ID of the incoming css data
    MsgCurrStatus cssConfInMsgId;                  //! [-] ID of the incoming css constellation data
    MsgCurrStatus cameraConfMsgId;                  //! [-] ID of the incoming camera  data
    std::vector <RWConfigLogSimMsg> rwInMessage;  //! [-] RW data message
    STSensorIntMsg STMessage;                 //! [-] ST data message
    std::vector <THROutputSimMsg> thrOutputMessage;         //! [-] Thr data message
    SCPlusStatesSimMsg scPlusMessage;         //! [-] s/c plus message
//    CSSArraySensorIntMsg cssDataMessage;          //! [-] CSS message
    CSSConfigFswMsg cssConfigMessage;          //! [-] CSS config
    CameraConfigMsg cameraConfigMessage;          //! [-] CSS config
    int32_t imageOutMsgID;                           //! ID for the outgoing Image message */
    int numRW;                                //! [-] Number of RW set in python
    int numThr;                               //! [-] Number of Thrusters set in python
}VizSpacecraftData;

/*! @brief Abstract class that is used to implement an effector impacting a GRAVITY body
           that does not itself maintain a state or represent a changing component of
           the body (for example: gravity, thrusters, solar radiation pressure, etc.)
 */
class VizInterface : public SysModel {
public:
    VizInterface();
    ~VizInterface();
    void SelfInit();
    void CrossInit();
    void Reset(uint64_t CurrentSimNanos);
    void UpdateState(uint64_t CurrentSimNanos);
    void ReadBSKMessages();
    void WriteProtobuffer(uint64_t CurrentSimNanos);

public:
    std::vector<VizSpacecraftData> scData; 

    uint64_t numSensors;
    int opNavMode;          //! [Bool] Set True if Unity/Viz couple in direct communication.
    int saveFile;           //! [Bool] Set True if Viz should save a file of the data.
    
    VizMsg viz_msg;
    //VizMsg viz_arch_buffer;
    std::string vizOutMsgName;
    int32_t vizOutMsgID;

    std::vector <std::string> spiceInMsgName; //! [-] Name of the incoming Spice data
    std::vector <std::string> planetNames;  //!< -- Names of planets we want to track, read in from python

    uint64_t numOutputBuffers;                //! [-] Number of buffers to request for the output messages
    
    uint64_t FrameNumber;                     //! Number of frames that have been updated for TimeStamp message
    std::string protoFilename;                     //! Filename for where to save the protobuff message

private:
    // ZeroMQ State
    void* context;
    void* requester_socket;


    std::vector<MsgCurrStatus>spiceInMsgID;                     //! [-] IDs of the incoming planets' spice data
    std::vector <SpicePlanetStateSimMsg> spiceMessage;      //! [-] Spice messages

    std::ofstream *outputStream;                       //! [-] Output file stream opened in reset
    
    std::map<uint32_t, SpicePlanetStateSimMsg> planetData; //!< -- Internal vector of planets
    
    
};

#endif /* VIZ_INTERFACE_H */
