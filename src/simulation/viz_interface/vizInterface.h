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

#include "../utilities/vizProtobuffer/vizMessage.pb.h"
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
#include "utilities/bskLogging.h"

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

// define Viz setting messages
typedef struct {
    std::string fromBodyName;   //!< [-] name of the body to start the line
    std::string toBodyName;     //!< [-] name of the body to point the line towards
    int lineColor[4];           //!< [-] desired RGBA as values between 0 and 255
}PointLine;

typedef struct {
    bool isKeepIn;              //!< True -> keep in cone created, False -> keep out cone created
    double position_B[3];       //!< [m] cone start relative to from body coordinate frame
    double normalVector_B[3];   //!< [-] cone normal direction vector
    double incidenceAngle;      //!< [deg] cone incidence angle
    double coneHeight;          //!< [m] sets height of visible cone (asthetic only, does not impact function)
    std::string fromBodyName;   //!< name of body to attach cone onto
    std::string toBodyName;     //!< [-] detect changes if this body has impingement on cone
    int coneColor[4];           //!< [-] desired RGBA as values between 0 and 255
    std::string coneName;       //!< [-] cone name, if unspecified, viz will autogenerate name
}KeepOutInCone;

typedef struct {
    std::string spacecraftName; //!< name of spacecraft onto which to place a camera
    int setMode;                //!< 0 -> body targeting, 1 -> pointing vector (default)
    double fieldOfView;         //!< rad, field of view setting, -1 -> use default, values between 0.0001 and 179.9999 deg valid
    std::string bodyTarget;     //!< Name of body camera should point to (default to first celestial body in messages). This is a setting for body targeting mode.
    int setView;                //!< 0 -> Nadir, 1 -> Orbit Normal, 2 -> Along Track (default to nadir). This is a setting for body targeting mode.
    double pointingVector_B[3]; //!< (default to 1, 0, 0). This is a setting for pointing vector mode.
}StdCameraSettings;

typedef struct {
    std::string spacecraftName; //!< Which spacecraft's camera 1
    int viewThrusterPanel;
    int viewThrusterHUD;
    int viewRWPanel;
    int viewRWHUD;
}ActuatorGuiSettings;

typedef struct {
    std::string modelPath;                  //!< Path to model obj -OR- "CUBE", "CYLINDER", or "SPHERE" to use a primitive shape
    std::vector<std::string> simBodiesToModify; //!< Which bodies in scene to replace with this model, use "ALL_SPACECRAFT" to apply custom model to all spacecraft in simulation
    double offset[3];                       //!< [m] offset to use to draw the model
    double rotation[3];                     //!< [rad] 3-2-1 Euler angles to rotate CAD about z, y, x axes
    double scale[3];                        //!< [] desired model scale in x, y, z in spacecraft CS
    std::string customTexturePath;          //!< (Optional) Path to texture to apply to model (note that a custom model's .mtl will be automatically imported with its textures during custom model import)
    std::string normalMapPath;              //!< (Optional) Path to the normal map for the customTexture
    int shader;                             //!< (Optional) Value of -1 to use viz default, 0 for Unity Specular Standard Shader, 1 for Unity Standard Shader
}CustomModel;

//! defines a data structure for the spacecraft components
typedef struct {
    std::string spacecraftName = "bsk-Sat";
    std::string cssDataInMsgName = "css_sensors_data";          //! [-] Name of the incoming css data
    std::string cssConfInMsgName = "css_config_data";           //! [-] Name of the incoming css constellation data
    std::string scPlusInMsgName = "inertial_state_output";      //! [-] Name of the incoming SCPlus data
    std::vector <std::string> rwInMsgName;                      //! [-] Name of the incoming rw data
    std::vector <ThrClusterMap> thrMsgData;                     //! [-] Name of the incoming thruster data
    std::string starTrackerInMsgName = "star_tracker_state";    //! [-] Name of the incoming Star Tracker data
    std::vector<MsgCurrStatus> rwInMsgID;                       //! [-] ID of the incoming rw data
    std::vector<MsgCurrStatus> thrMsgID;                        //! [-] ID of the incoming thruster data
    MsgCurrStatus starTrackerInMsgID;                           //! [-] ID of the incoming Star Tracker data
    MsgCurrStatus scPlusInMsgID;                                //! [-] ID of the incoming SCPlus data
    MsgCurrStatus cssDataInMsgId;                               //! [-] ID of the incoming css data
    MsgCurrStatus cssConfInMsgId;                               //! [-] ID of the incoming css constellation data
    std::vector <RWConfigLogSimMsg> rwInMessage;                //! [-] RW data message
    STSensorIntMsg STMessage;                                   //! [-] ST data message
    std::vector <THROutputSimMsg> thrOutputMessage;             //! [-] Thr data message
    SCPlusStatesSimMsg scPlusMessage;                           //! [-] s/c plus message
//    CSSArraySensorIntMsg cssDataMessage;                      //! [-] CSS message
    CSSConfigFswMsg cssConfigMessage;                           //! [-] CSS config
    int numRW = 0;                                              //! [-] Number of RW set in python
    int numThr = 0;                                             //! [-] Number of Thrusters set in python
}VizSpacecraftData;

typedef struct {
    double      ambient;        //!< [-] Ambient background lighting. Should be a value between 0 and 8.  A value of -1 means it is not set.
    int32_t     orbitLinesOn;   //! toogle for showing orbit lines (-1, 0, 1)
    int32_t     spacecraftCSon; //! toogle for showing spacecraft CS (-1, 0, 1)
    int32_t     planetCSon;     //! toogle for showing planet CS (-1, 0, 1)
    std::vector<PointLine> pointLineList;   //! vector of powerLine structures
    std::vector<KeepOutInCone> coneList;    //! vector of keep in/out cones
    std::vector<StdCameraSettings> stdCameraList; //! vector of spacecraft cameras
    std::vector<CustomModel> customModelList;  //! vector of custom object models
    std::vector<ActuatorGuiSettings> actuatorGuiSettingsList; //! msg containing the flags on displaying the actuator GUI elements
    std::string skyBox;         //! string containing the star field options, '' provides default NASA SVS Starmap, "ESO" use ESO Milky Way skybox, "black" provides a black background, or provide a filepath to custom background
    bool        dataFresh;      //!< [-] flag indicating if the settings have been transmitted,
}VizSettings;


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
    std::vector<VizSpacecraftData> scData;      //! [-] vector of spacecraft data containers
    std::vector <std::string> spiceInMsgName;   //! [-] Name of the incoming Spice data
    std::string opnavImageOutMsgName;           //! The name of the Image output message*/
    int opNavMode;                              //! [int] Set non-zero positive value  if Unity/Viz couple in direct communication. (1 - regular opNav, 2 - performance opNav)
    bool saveFile;                              //! [Bool] Set True if Vizard should save a file of the data.
    bool liveStream;                            //! [Bool] Set True if Vizard should receive a live stream of BSK data.
    void* bskImagePtr;                          //! [RUN] Permanent pointer for the image to be used in BSK without relying on ZMQ because ZMQ will free it (whenever, who knows)

    std::string cameraConfInMsgName = "camera_config_data";     //! [-] Name of the incoming camera data
    MsgCurrStatus cameraConfMsgId;                              //! [-] ID of the incoming camera  data
    CameraConfigMsg cameraConfigMessage;                        //! [-] Camera config
    
    std::vector <std::string> planetNames;      //!< -- Names of planets we want to track, read in from python

    uint64_t numOutputBuffers;                  //! [-] Number of buffers to request for the output messages
    
    int64_t FrameNumber;                        //! Number of frames that have been updated for TimeStamp message
    std::string protoFilename;                  //! Filename for where to save the protobuff message
    VizSettings settings;                       //! [-] container for the Viz settings that can be specified from BSK

    BSKLogger bskLogger;                        //!< -- BSK Logging


private:
    // ZeroMQ State
    void* context;
    void* requester_socket;
    int firstPass;                              //! Flag to intialize the viz at first timestep */

    int32_t imageOutMsgID;                      //! ID for the outgoing Image message */
    std::vector<MsgCurrStatus>spiceInMsgID;     //! [-] IDs of the incoming planets' spice data
    std::vector <SpicePlanetStateSimMsg> spiceMessage;//! [-] Spice messages
    std::ofstream *outputStream;                //! [-] Output file stream opened in reset
    
    std::map<uint32_t, SpicePlanetStateSimMsg> planetData; //!< -- Internal vector of planets
    
};

#endif /* VIZ_INTERFACE_H */
