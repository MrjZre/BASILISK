''' '''
'''
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

'''
import math
from Basilisk.utilities import macros as mc
from Basilisk.fswAlgorithms import (vehicleConfigData, hillPoint, inertial3D, attTrackingError, MRP_Feedback,
                                    rwConfigData, rwMotorTorque, fswMessages)


class BSKFswModels():
    def __init__(self, SimBase):
        # Define process name and default time-step for all FSW tasks defined later on
        self.processName = SimBase.FSWProcessName
        self.processTasksTimeStep = mc.sec2nano(0.1)  # 0.5

        # Create module data and module wraps
        self.vehicleData = vehicleConfigData.VehConfigInputData()
        self.vehicleWrap = SimBase.setModelDataWrap(self.vehicleData)
        self.vehicleWrap.ModelTag = "vehicleConfiguration"

        self.inertial3DData = inertial3D.inertial3DConfig()
        self.inertial3DWrap = SimBase.setModelDataWrap(self.inertial3DData)
        self.inertial3DWrap.ModelTag = "inertial3D"

        self.hillPointData = hillPoint.hillPointConfig()
        self.hillPointWrap = SimBase.setModelDataWrap(self.hillPointData)
        self.hillPointWrap.ModelTag = "hillPoint"

        self.trackingErrorData = attTrackingError.attTrackingErrorConfig()
        self.trackingErrorWrap = SimBase.setModelDataWrap(self.trackingErrorData)
        self.trackingErrorWrap.ModelTag = "trackingError"

        self.mrpFeedbackControlData = MRP_Feedback.MRP_FeedbackConfig()
        self.mrpFeedbackControlWrap = SimBase.setModelDataWrap(self.mrpFeedbackControlData)
        self.mrpFeedbackControlWrap.ModelTag = "mrpFeedbackControl"


        self.mrpFeedbackRWsData = MRP_Feedback.MRP_FeedbackConfig()
        self.mrpFeedbackRWsWrap = SimBase.setModelDataWrap(self.mrpFeedbackRWsData)
        self.mrpFeedbackRWsWrap.ModelTag = "mrpFeedbackRWs"

        self.rwConfigData = rwConfigData.rwConfigData_Config()
        self.rwConfigWrap = SimBase.setModelDataWrap(self.rwConfigData)
        self.rwConfigWrap.ModelTag = "rwConfigData"

        self.rwMotorTorqueData = rwMotorTorque.rwMotorTorqueConfig()
        self.rwMotorTorqueWrap = SimBase.setModelDataWrap(self.rwMotorTorqueData)
        self.rwMotorTorqueWrap.ModelTag = "rwMotorTorque"

        # Initialize all modules
        self.InitAllFSWObjects(SimBase)

        # Create tasks
        SimBase.fswProc.addTask(SimBase.CreateNewTask("initOnlyTask", int(1E10)), 1)
        SimBase.fswProc.addTask(SimBase.CreateNewTask("inertial3DPointTask", self.processTasksTimeStep), 20)
        SimBase.fswProc.addTask(SimBase.CreateNewTask("hillPointTask", self.processTasksTimeStep), 20)
        SimBase.fswProc.addTask(SimBase.CreateNewTask("mrpFeedbackTask", self.processTasksTimeStep), 10)
        SimBase.fswProc.addTask(SimBase.CreateNewTask("RWAEffectorSet", self.processTasksTimeStep), 102)

        # Assign initialized modules to tasks
        SimBase.AddModelToTask("initOnlyTask", self.vehicleWrap, self.vehicleData, 2)
        SimBase.AddModelToTask("initOnlyTask", self.rwConfigWrap, self.rwConfigData, 1)

        SimBase.AddModelToTask("inertial3DPointTask", self.inertial3DWrap, self.inertial3DData, 10)
        SimBase.AddModelToTask("inertial3DPointTask", self.trackingErrorWrap, self.trackingErrorData, 9)

        SimBase.AddModelToTask("hillPointTask", self.hillPointWrap, self.hillPointData, 10)
        SimBase.AddModelToTask("hillPointTask", self.trackingErrorWrap, self.trackingErrorData, 9)

        SimBase.AddModelToTask("mrpFeedbackTask", self.mrpFeedbackControlWrap, self.mrpFeedbackControlData, 10)

        SimBase.AddModelToTask("RWAEffectorSet", self.mrpFeedbackRWsWrap, self.mrpFeedbackRWsData, 9)
        SimBase.AddModelToTask("RWAEffectorSet", self.rwMotorTorqueWrap, self.rwMotorTorqueData, 8)
        #masterSim.AddModelToTask("RWAEffectorSet", self.RWANullSpaceDataWrap,self.RWANullSpaceData, 7)

        # Create events to be called for triggering GN&C maneuvers
        SimBase.fswProc.disableAllTasks()
        SimBase.createNewEvent("initiateAttitudeGuidance", self.processTasksTimeStep, True,
                               ["self.modeRequest == 'inertial3D'"],
                               ["self.fswProc.disableAllTasks()",
                                "self.enableTask('inertial3DPointTask')",
                                "self.enableTask('mrpFeedbackTask')"])

        SimBase.createNewEvent("initiateHillPoint", self.processTasksTimeStep, True,
                               ["self.modeRequest == 'hillPoint'"],
                               ["self.fswProc.disableAllTasks()",
                                "self.enableTask('hillPointTask')",
                                "self.enableTask('mrpFeedbackTask')"])

        SimBase.createNewEvent("initiateFeedbackRW", self.processTasksTimeStep, True,
                               ["self.modeRequest == 'feedbackRW'"],
                               ["self.fswProc.disableAllTasks()",
                                "self.enableTask('inertial3DPointTask')",
                                "self.enableTask('RWAEffectorSet')"])

    # ------------------------------------------------------------------------------------------- #
    # These are module-initialization methods
    def SetInertial3DPointGuidance(self):
        self.inertial3DData.sigma_R0N = [0.2, 0.4, 0.6]
        self.inertial3DData.outputDataName = "referenceOut"

    def SetHillPointGuidance(self, SimBase):
        self.hillPointData.outputDataName = "referenceOut"
        self.hillPointData.inputNavDataName = SimBase.DynModels.simpleNavObject.outputTransName
        self.hillPointData.inputCelMessName = SimBase.DynModels.earthGravBody.bodyInMsgName[:-12]

    def SetAttitudeTrackingError(self, SimBase):
        self.trackingErrorData.inputNavName = SimBase.DynModels.simpleNavObject.outputAttName
        # Note: SimBase.DynModels.simpleNavObject.outputAttName = "simple_att_nav_output"
        self.trackingErrorData.inputRefName = "referenceOut"
        self.trackingErrorData.outputDataName = "guidanceOut"

    def SetMRPFeedbackControl(self, SimBase):
        self.mrpFeedbackControlData.inputGuidName = "guidanceOut"
        self.mrpFeedbackControlData.vehConfigInMsgName = "adcs_config_data"
        self.mrpFeedbackControlData.outputDataName =  SimBase.DynModels.extForceTorqueObject.cmdTorqueInMsgName
        # Note: SimBase.DynModels.extForceTorqueObject.cmdTorqueInMsgName = "extTorquePntB_B_cmds"

        self.mrpFeedbackControlData.K = 3.5
        self.mrpFeedbackControlData.Ki = -1.0 # Note: make value negative to turn off integral feedback
        self.mrpFeedbackControlData.P = 30.0
        self.mrpFeedbackControlData.integralLimit = 2. / self.mrpFeedbackControlData.Ki * 0.1
        self.mrpFeedbackControlData.domega0 = [0.0, 0.0, 0.0]


    def SetMRPFeedbackRWA(self):
        self.mrpFeedbackRWsData.K = 3.5
        self.mrpFeedbackRWsData.Ki = -1  # Note: make value negative to turn off integral feedback
        self.mrpFeedbackRWsData.P = 30.0
        self.mrpFeedbackRWsData.integralLimit = 2. / self.mrpFeedbackRWsData.Ki * 0.1
        self.mrpFeedbackRWsData.domega0 = [0.0, 0.0, 0.0]

        self.mrpFeedbackRWsData.vehConfigInMsgName = "adcs_config_data"
        self.mrpFeedbackRWsData.inputRWSpeedsName = "reactionwheel_output_states" # DynModels.rwStateEffector.OutputDataString
        self.mrpFeedbackRWsData.rwParamsInMsgName = "rwa_config_data_parsed"
        self.mrpFeedbackRWsData.inputGuidName = "guidanceOut"
        self.mrpFeedbackRWsData.outputDataName = "controlTorqueRaw"


    def SetVehicleConfiguration(self, SimBase):
        # self.vehicleData.ISCPntB_B = SimBase.DynClass.I_sc
        self.vehicleData.ISCPntB_B = [900.0, 0.0, 0.0, 0.0, 800.0, 0.0, 0.0, 0.0, 600.0]
        self.vehicleData.CoM_B = [0.0, 0.0, 1.0]
        self.vehicleData.outputPropsName = "adcs_config_data"

    def SetLocalConfigData(self, SimBase):
        # Configure RW pyramid exactly as it is in the Dynamics (i.e. FSW with perfect knowledge)
        self.RWAGsMatrix = []
        self.RWAJsList = []
        rwElAngle = 42.5 * math.pi / 180.0
        rwClockAngle = 45.0 * math.pi / 180.0
        wheelJs = 50.0 / (6000.0 / 60.0 * math.pi * 2.0)
        # -- RW 1
        self.RWAGsMatrix.extend([math.sin(rwElAngle) * math.sin(rwClockAngle),
                                 math.sin(rwElAngle) * math.cos(rwClockAngle), -math.cos(rwElAngle)])
        rwClockAngle += 90.0 * math.pi / 180.0
        self.RWAJsList.extend([wheelJs])
        # -- RW 2
        self.RWAGsMatrix.extend([math.sin(rwElAngle) * math.sin(rwClockAngle),
                                 -math.sin(rwElAngle) * math.cos(rwClockAngle), math.cos(rwElAngle)])
        rwClockAngle += 180.0 * math.pi / 180.0
        self.RWAJsList.extend([wheelJs])
        # -- RW 3
        self.RWAGsMatrix.extend([math.sin(rwElAngle) * math.sin(rwClockAngle),
                                 math.sin(rwElAngle) * math.cos(rwClockAngle), -math.cos(rwElAngle)])
        rwClockAngle -= 90.0 * math.pi / 180.0
        self.RWAJsList.extend([wheelJs])
        # -- RW 4
        self.RWAGsMatrix.extend([math.sin(rwElAngle) * math.sin(rwClockAngle),
                                 -math.sin(rwElAngle) * math.cos(rwClockAngle), math.cos(rwElAngle)])
        self.RWAJsList.extend([wheelJs])

        # Create the messages necessary to make FSW aware of the pyramid configuration
        i = 0
        rwClass = vehicleConfigData.RWConstellationFswMsg()
        rwPointer = vehicleConfigData.RWConfigElementFswMsg()
        rwClass.numRW = 4
        while (i < 4):
            rwPointer.gsHat_B = self.RWAGsMatrix[i * 3:i * 3 + 3]
            rwPointer.Js = self.RWAJsList[i]
            vehicleConfigData.RWConfigArray_setitem(rwClass.reactionWheels, i, rwPointer)
            i += 1
        SimBase.TotalSim.CreateNewMessage("FSWProcess", "rwa_config_data",
                                            fswMessages.MAX_EFF_CNT * 4 * 8 + 8, 2, "RWConstellation")
        SimBase.TotalSim.WriteMessageData("rwa_config_data", fswMessages.MAX_EFF_CNT * 4 * 8 + 8, 0, rwClass)

    def SetRWConfigDataFSW(self):
        self.rwConfigData.rwConstellationInMsgName = "rwa_config_data"
        self.rwConfigData.vehConfigInMsgName = "adcs_config_data"
        self.rwConfigData.rwParamsOutMsgName = "rwa_config_data_parsed"

    def SetRWMotorTorque(self):
        controlAxes_B = [
            1.0, 0.0, 0.0
            , 0.0, 1.0, 0.0
            , 0.0, 0.0, 1.0
        ]
        self.rwMotorTorqueData.controlAxes_B = controlAxes_B
        self.rwMotorTorqueData.inputVehControlName = "controlTorqueRaw" # message from your control law
        self.rwMotorTorqueData.outputDataName = "reactionwheel_cmds"#"reactionwheel_cmds_raw"
        self.rwMotorTorqueData.rwParamsInMsgName = "rwa_config_data_parsed"

    # Global call to initialize every module
    def InitAllFSWObjects(self, SimBase):
        self.SetInertial3DPointGuidance()
        self.SetHillPointGuidance(SimBase)
        self.SetAttitudeTrackingError(SimBase)
        self.SetMRPFeedbackControl(SimBase)
        self.SetVehicleConfiguration(SimBase)
        self.SetLocalConfigData(SimBase)
        self.SetMRPFeedbackRWA()
        self.SetRWConfigDataFSW()
        self.SetRWMotorTorque()


#BSKFswModels()