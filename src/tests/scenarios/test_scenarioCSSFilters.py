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

#
# Basilisk Scenario Script and Integrated Test
#
# Purpose:  Demonstrates how to setup and use sun heading filters
# Author:   Thibaud Teil
# Creation Date:  November 20, 2017
#



import pytest
import numpy as np
import time

from Basilisk import __path__
bskPath = __path__[0]

from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
import matplotlib.pyplot as plt
from Basilisk.utilities import macros
from Basilisk.simulation import coarse_sun_sensor
from Basilisk.utilities import orbitalMotion as om
from Basilisk.utilities import RigidBodyKinematics as rbk

from Basilisk.fswAlgorithms import cssComm

from Basilisk.simulation import spacecraftPlus
from Basilisk.simulation import spice_interface
from Basilisk.fswAlgorithms import vehicleConfigData
from Basilisk.fswAlgorithms import sunlineUKF
from Basilisk.fswAlgorithms import sunlineEKF
from Basilisk.fswAlgorithms import okeefeEKF
import SunLineEKF_test_utilities as Fplot

# The following 'parametrize' function decorator provides the parameters and expected results for each
#   of the multiple test runs for this test.
@pytest.mark.parametrize("FilterType, simTime", [
      ('uKF', 200)
    , ('EKF', 200)
    , ('OEKF', 200)
])

# provide a unique test method name, starting with test_
def test_Filters(show_plots, FilterType, simTime):
    '''This function is called by the py.test environment.'''
    # each test method requires a single assert method to be called
    [testResults, testMessage] = run(show_plots, FilterType, simTime)
    assert testResults < 1, testMessage


def setupUKFData(filterObject):
    filterObject.navStateOutMsgName = "sunline_state_estimate"
    filterObject.filtDataOutMsgName = "sunline_filter_data"
    filterObject.cssDataInMsgName = "css_sensors_data"
    filterObject.cssConfInMsgName = "css_config_data"

    filterObject.alpha = 0.02
    filterObject.beta = 2.0
    filterObject.kappa = 0.0

    filterObject.state = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    filterObject.covar = [0.2, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.2, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.2, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.02, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.02, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.02]
    qNoiseIn = np.identity(6)
    qNoiseIn[0:3, 0:3] = qNoiseIn[0:3, 0:3]*0.017*0.017
    qNoiseIn[3:6, 3:6] = qNoiseIn[3:6, 3:6]*0.0017*0.0017
    filterObject.qNoise = qNoiseIn.reshape(36).tolist()
    filterObject.qObsVal = 0.017*0.017

def setupEKFData(filterObject):
    filterObject.navStateOutMsgName = "sunline_state_estimate"
    filterObject.filtDataOutMsgName = "sunline_filter_data"
    filterObject.cssDataInMsgName = "css_sensors_data"
    filterObject.cssConfInMsgName = "css_config_data"

    filterObject.sensorUseThresh = 0.
    filterObject.states = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    filterObject.x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    filterObject.covar = [0.2, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.2, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.2, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.002, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.002, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.002]

    filterObject.qProcVal = 0.001**2
    filterObject.qObsVal = 0.017 ** 2
    filterObject.eKFSwitch = 3. #If low (0-5), the CKF kicks in easily, if high (>10) it's mostly only EKF

def setupOEKFData(filterObject):
    filterObject.navStateOutMsgName = "sunline_state_estimate"
    filterObject.filtDataOutMsgName = "sunline_filter_data"
    filterObject.cssDataInMsgName = "css_sensors_data"
    filterObject.cssConfInMsgName = "css_config_data"

    filterObject.sensorUseThresh = 0.
    filterObject.omega = [0., 0., 0.]
    filterObject.states = [1.0, 0.0, 0.0]
    filterObject.x = [0.0, 0.0, 0.0]
    filterObject.covar = [0.2, 0.0, 0.0,
                          0.0, 0.2, 0.0,
                          0.0, 0.0, 0.2]

    filterObject.qProcVal = 0.1**2
    filterObject.qObsVal = 0.017 ** 2
    filterObject.eKFSwitch = 3. #If low (0-5), the CKF kicks in easily, if high (>10) it's mostly only EKF


## \defgroup Tutorials_2_4
##   @{
## Demonstrates how Estimate spacecraft attitude using Coarse Sun Sensors Filters.
#
# Coarse Sun Sensor (CSS) Filters {#scenarioCSSFilters}
# ====
#
# Scenario Description
# -----
# This script sets up a 6-DOF spacecraft in deep space without any gravitational bodies. Only rotational
# motion is simulated.  The script illustrates how to setup attitude filters that use measurements from the Coarse Sun Sensors (CSS).
# A constellation of CSS are setup, and different filters are used to compare their performances.
#
# Setup | Filter               |
# ----- | -------------------- |
# 1     | uKF                  |
# 2     | EKF                  |
# 3     | EKF V2               |
#
# To run the default scenario, call the python script through
#
#       python test_scenarioCSSFilters.py
#
# When the simulation completes several plots are written summarizing the filter performances.
#
# The dynamics simulation is setup using a SpacecraftPlus() module where a specific spacecraft location
# is specified.  Note that both the rotational and translational degrees of
# freedom of the spacecraft hub are turned on here to get a 6-DOF simulation.  The position
# vector is required when computing the relative heading between the sun and the spacecraft locations.  The
# spacecraft position is held fixed, while the orientation rotates constantly about the 3rd body axis.
# ~~~~~~~~~~~~~~~~{.py}
#     scObject.hub.r_CN_NInit = [[-om.AU*1000.], [0.0], [0.0]]        # m   - r_CN_N
#     scObject.hub.v_CN_NInit = [[0.0], [0.0], [0.0]]                 # m/s - v_CN_N
#     scObject.hub.sigma_BNInit = [[0.0], [0.0], [0.0]]               # sigma_BN_B
#     scObject.hub.omega_BN_BInit = [[0.5*macros.D2R], [-1.*macros.D2R], [1.*macros.D2R]]   # rad/s - omega_BN_B
# ~~~~~~~~~~~~~~~~
#
# The CSS modules must first be individual created and configured.
# In this simulation each case uses two CSS sensors.  The minimum variables that must be set for each CSS
# includes:
# ~~~~~~~~~~~~~~~~{.py}
# cssConstelation = coarse_sun_sensor.CSSConstellation()
# for CSSHat in CSSOrientationList:
#     newCSS = coarse_sun_sensor.CoarseSunSensor()
#     newCSS.nHat_B = CSSHat
#     cssConstelation.appendCSS(newCSS)
# cssConstelation.outputConstellationMessage = 'css_sensors_data'
# scSim.AddModelToTask(simTaskName, cssConstelation)
# ~~~~~~~~~~~~~~~~
#
# The constellation characteristics are summarized in the following table.
#
# CSS   | nomral vector          |
# ----- | ---------------------- |
# 1     | [sqrt(2)/2, -0.5, 0.5] |
# 2     | [sqrt(2)/2, -0.5, -0.5]|
# 3     | [sqrt(2)/2, 0.5, -0.5] |
# 4     | [sqrt(2)/2,  0.5, 0.5] |
# 5     | [-sqrt(2)/2, 0, sqrt(2)/2] |
# 6     | [-sqrt(2)/2, sqrt(2)/2, 0] |
# 7     | [-sqrt(2)/2, 0, -sqrt(2)/2] |
# 8     | [-sqrt(2)/2, -sqrt(2)/2, 0] |
#
#
# An additional message must be written for the configuration of the CSS. This is done with vehicleConfigData
# ~~~~~~~~~~~~~~~~{.py}
# cssConstVehicle = vehicleConfigData.CSSConstConfig()
#
# totalCSSList = []
# for CSSHat in CSSOrientationList:
#     newCSS = vehicleConfigData.CSSConfigurationElement()
#     newCSS.nHat_B = CSSHat
#     totalCSSList.append(newCSS)
# cssConstVehicle.nCSS = len(CSSOrientationList)
# cssConstVehicle.cssVals = totalCSSList
#
# ~~~~~~~~~~~~~~~~
# This allows us to write the messages as follows:
# ~~~~~~~~~~~~~~~~{.py}
#
# msgSize = cssConstVehicle.getStructSize()
# inputData = cssComm.CSSArraySensorIntMsg()
#
# inputMessageSize = inputData.getStructSize()
# scSim.TotalSim.CreateNewMessage(simProcessName, "css_config_data",
#                                 msgSize, 2, "CSSConstConfig")
# scSim.TotalSim.CreateNewMessage(simProcessName, moduleConfig.cssDataInMsgName, inputMessageSize,
#                                 2)  # number of buffers (leave at 2 as default, don't make zero)
# scSim.TotalSim.WriteMessageData("css_config_data", msgSize, 0, cssConstVehicle)
# ~~~~~~~~~~~~~~~~
#
# This sets up the spacecraft, it's sun sensors, and the sun direction. The filters can now be initialized.
# These are configured very similarly, but the nature of the filters lead to slight differences.
#
#
# Setup 1 - ukF
# -----
#
# In the first run, we use an unscented Kalman Filter. This filter has the following states:
#
# States         |     notation |
# -------------- | ------------ |
# Sunheading     |      d       |
# Sunheading Rate|      d_dot   |
#
# This filter estimates sunheading, and the sunheading's rate of change. As a unscented filter, it also has the
# the following parameters:
#
#
# Name       | Value        |
# -----------| ------------ |
# alpha      |    0.02      |
# beta       |      2       |
# kappa      |      0       |
#
# The covariance is then set, as well as the measurement noise:
#
#
# Parameter                                 |       Value       |
# ----------------------------------------  | ----------------- |
# covariance on  heading vector  components |       0.2         |
# covariance on heading rate  components    |       0.02        |
# noise on heading measurements             |       0.017 ** 2  |
# noise on heading measurements             |       0.0017 ** 2 |
#
#
# This is all initialized in the following code
#  ~~~~~~~~~~~~~{.py}
# filterObject.navStateOutMsgName = "sunline_state_estimate"
# filterObject.filtDataOutMsgName = "sunline_filter_data"
# filterObject.cssDataInMsgName = "css_sensors_data"
# filterObject.cssConfInMsgName = "css_config_data"
#
# filterObject.alpha = 0.02
# filterObject.beta = 2.0
# filterObject.kappa = 0.0
#
# filterObject.state = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
# filterObject.covar = [0.2, 0.0, 0.0, 0.0, 0.0, 0.0,
#                       0.0, 0.2, 0.0, 0.0, 0.0, 0.0,
#                       0.0, 0.0, 0.2, 0.0, 0.0, 0.0,
#                       0.0, 0.0, 0.0, 0.02, 0.0, 0.0,
#                       0.0, 0.0, 0.0, 0.0, 0.02, 0.0,
#                       0.0, 0.0, 0.0, 0.0, 0.0, 0.02]
# qNoiseIn = np.identity(6)
# qNoiseIn[0:3, 0:3] = qNoiseIn[0:3, 0:3] * 0.017 * 0.017
# qNoiseIn[3:6, 3:6] = qNoiseIn[3:6, 3:6] * 0.0017 * 0.0017
# filterObject.qNoise = qNoiseIn.reshape(36).tolist()
# filterObject.qObsVal = 0.017 * 0.017
# ~~~~~~~~~~~~~
#
# The resulting plots of the states, their covariance envelopes, as compared to the true state
# are plotted. Further documentation can be found in the _Documentation folder in the module directory.
# ![uKF Performance](Images/Scenarios/scenario_Filters_StatesExpecteduKF.svg "States vs Truth")
#
# Setup 2 - EKF
# ------
#
# The following filter tested is an Extended Kalman filter. This filter uses all the same values for intialization
#  as the uKF (aside from the uKF specific alpha, beta, kappa variables). A couple variables are added:
#
# Name          | Value        |
# -----------   | ------------ |
# Process noise |    0.1**2    |
# CKF switch    |      3       |
#
# The process noise is the noise added on the dynamics. This allows to account for dynamical uncertainties, and
# avoid filter saturation.
#
# The CKF switch is the number of measurements that are processed using a classical, linear Kalman filter when the
# filter is first run. This allows for the covariance to shrink before employing the EKF, increasing the robustness.
#
# These variables are setup as follows:
# ~~~~~~~~~~~~~{.py}
# filterObject.navStateOutMsgName = "sunline_state_estimate"
# filterObject.filtDataOutMsgName = "sunline_filter_data"
# filterObject.cssDataInMsgName = "css_sensors_data"
# filterObject.cssConfInMsgName = "css_config_data"
#
# filterObject.sensorUseThresh = 0.
# filterObject.states = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
# filterObject.x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
# filterObject.covar = [0.2, 0.0, 0.0, 0.0, 0.0, 0.0,
#                       0.0, 0.2, 0.0, 0.0, 0.0, 0.0,
#                       0.0, 0.0, 0.2, 0.0, 0.0, 0.0,
#                       0.0, 0.0, 0.0, 0.002, 0.0, 0.0,
#                       0.0, 0.0, 0.0, 0.0, 0.002, 0.0,
#                       0.0, 0.0, 0.0, 0.0, 0.0, 0.002]
#
# filterObject.qProcVal = 0.1 ** 2
# filterObject.qObsVal = 0.017 ** 2
# filterObject.eKFSwitch = 3.  # If low (0-5), the CKF kicks in easily, if high (>10) it's mostly only EKF
# ~~~~~~~~~~~~~
# The states vs expected states are plotted, as well as the state error plots along with the covariance
# envelopes. Further documentation can be found in the _Documentation folder in the module directory.
# ![EKF State Errors](Images/Scenarios/scenario_Filters_StatesPlotEKF.svg "State Error and Covariances")
# ![EKF Filter performance](Images/Scenarios/scenario_Filters_StatesExpectedEKF.svg "States vs Truth")
#
# Setup 3 -OEKF
# ------
#
# The 3rd scenario uses a second type of Extended Kalman Filter (named Okeefe-EKF). This filter takes in fewer states
# as it only estimates the sunheading. In order to propagate it, it estimates the omega vector from the two last
# measurements.
#
# Further documentation can be found in the _Documentation folder in the module directory. The set up is done as follows:
#
# ~~~~~~~~~~~~~{.py}
# filterObject.navStateOutMsgName = "sunline_state_estimate"
# filterObject.filtDataOutMsgName = "sunline_filter_data"
# filterObject.cssDataInMsgName = "css_sensors_data"
# filterObject.cssConfInMsgName = "css_config_data"
#
# filterObject.sensorUseThresh = 0.
# filterObject.omega = [0., 0., 0.]
# filterObject.states = [1.0, 0.0, 0.0]
# filterObject.x = [0.0, 0.0, 0.0]
# filterObject.covar = [0.2, 0.0, 0.0,
#                       0.0, 0.2, 0.0,
#                       0.0, 0.0, 0.2]
#
# filterObject.qProcVal = 0.1 ** 2
# filterObject.qObsVal = 0.017 ** 2
# filterObject.eKFSwitch = 3.  # If low (0-5), the CKF kicks in easily, if high (>10) it's mostly only EKF
# ~~~~~~~~~~~~~
# The results from this filter are plotted:
# ![OEKF State Errors](Images/Scenarios/scenario_Filters_StatesPlotOEKF.svg "State Error and Covariances")
# ![OEKF Filter performance](Images/Scenarios/scenario_Filters_StatesExpectedOEKF.svg "States vs Truth")
#

##  @}
def run(show_plots, FilterType, simTime):
    '''Call this routine directly to run the tutorial scenario.'''
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages

    #
    #  From here on there scenario python code is found.  Above this line the code is to setup a
    #  unitTest environment.  The above code is not critical if learning how to code BSK.
    #

    # Create simulation variable names
    simTaskName = "simTask"
    simProcessName = "simProcess"

    #  Create a sim module as an empty container
    scSim = SimulationBaseClass.SimBaseClass()
    scSim.TotalSim.terminateSimulation()

    # set the simulation time variable used later on
    simulationTime = macros.sec2nano(simTime)

    #
    #  create the simulation process
    #
    dynProcess = scSim.CreateNewProcess(simProcessName)

    # create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(1.)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    #
    #   setup the simulation tasks/objects
    #
    spiceObject = spice_interface.SpiceInterface()
    spiceObject.planetNames = spice_interface.StringVector(["sun"])
    spiceObject.ModelTag = "SpiceInterfaceData"
    spiceObject.SPICEDataPath = bskPath + '/supportData/EphemerisData/'
    spiceObject.outputBufferCount = 100000
    spiceObject.UTCCalInit = '2021 MAY 04 07:47:49.965 (UTC)'

    scSim.TotalSim.logThisMessage('sun_planet_data', simulationTimeStep)
    scSim.AddModelToTask(simTaskName, spiceObject)


    # initialize spacecraftPlus object and set properties
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "spacecraftBody"
    # define the simulation inertia
    I = [900., 0., 0.,
         0., 800., 0.,
         0., 0., 600.]
    scObject.hub.mHub = 750.0                   # kg - spacecraft mass
    scObject.hub.r_BcB_B = [[0.0], [0.0], [0.0]] # m - position vector of body-fixed point B relative to CM
    scObject.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)
    scObject.hub.useTranslation = True
    scObject.hub.useRotation = True

    #
    # set initial spacecraft states
    #
    scObject.hub.r_CN_NInit = [[-om.AU*1000.], [0.0], [0.0]]              # m   - r_CN_N
    scObject.hub.v_CN_NInit = [[0.0], [0.0], [0.0]]                 # m/s - v_CN_N
    scObject.hub.sigma_BNInit = [[0.0], [0.0], [0.0]]               # sigma_BN_B
    scObject.hub.omega_BN_BInit = [[0.5*macros.D2R], [-1.*macros.D2R], [1.*macros.D2R]]   # rad/s - omega_BN_B

    scSim.TotalSim.logThisMessage('inertial_state_output', simulationTimeStep)
    # add spacecraftPlus object to the simulation process
    scSim.AddModelToTask(simTaskName, scObject)

    # Make a CSS constelation
    cssConstelation = coarse_sun_sensor.CSSConstellation()
    CSSOrientationList = [
        [0.70710678118654746, -0.5, 0.5],
        [0.70710678118654746, -0.5, -0.5],
        [0.70710678118654746, 0.5, -0.5],
        [0.70710678118654746, 0.5, 0.5],
        [-0.70710678118654746, 0, 0.70710678118654757],
        [-0.70710678118654746, 0.70710678118654757, 0.0],
        [-0.70710678118654746, 0, -0.70710678118654757],
        [-0.70710678118654746, -0.70710678118654757, 0.0],
    ]
    for CSSHat in CSSOrientationList:
        newCSS = coarse_sun_sensor.CoarseSunSensor()
        newCSS.nHat_B = CSSHat
        cssConstelation.appendCSS(newCSS)
    cssConstelation.outputConstellationMessage = 'css_sensors_data'
    scSim.AddModelToTask(simTaskName, cssConstelation)

    #
    #   Add the normals to the vehicle Config data struct
    #
    cssConstVehicle = vehicleConfigData.CSSConstConfig()

    totalCSSList = []
    for CSSHat in CSSOrientationList:
        newCSS = vehicleConfigData.CSSConfigurationElement()
        newCSS.nHat_B = CSSHat
        totalCSSList.append(newCSS)
    cssConstVehicle.nCSS = len(CSSOrientationList)
    cssConstVehicle.cssVals = totalCSSList
    #
    # Setup filter
    #
    if FilterType == 'EKF':
        moduleConfig = sunlineEKF.sunlineEKFConfig()
        moduleWrap = scSim.setModelDataWrap(moduleConfig)
        moduleWrap.ModelTag = "SunlineEKF"
        setupEKFData(moduleConfig)

        # Add test module to runtime call list
        scSim.AddModelToTask(simTaskName, moduleWrap, moduleConfig)

        statesString = 'SunlineEKF.states'
        covarString = 'SunlineEKF.covar'
        scSim.AddVariableForLogging('SunlineEKF.x', simulationTimeStep, 0, 5)

    if FilterType == 'OEKF':
        moduleConfig = okeefeEKF.okeefeEKFConfig()
        moduleWrap = scSim.setModelDataWrap(moduleConfig)
        moduleWrap.ModelTag = "okeefeEKF"
        setupOEKFData(moduleConfig)

        # Add test module to runtime call list
        scSim.AddModelToTask(simTaskName, moduleWrap, moduleConfig)

        statesString = 'okeefeEKF.states'
        covarString = 'okeefeEKF.covar'
        scSim.AddVariableForLogging('okeefeEKF.x', simulationTimeStep, 0, 2)

    if FilterType == 'uKF':
        moduleConfig = sunlineUKF.SunlineUKFConfig()
        moduleWrap = scSim.setModelDataWrap(moduleConfig)
        moduleWrap.ModelTag = "SunlineUKF"
        setupUKFData(moduleConfig)

        # Add test module to runtime call list
        scSim.AddModelToTask(simTaskName, moduleWrap, moduleConfig)

        statesString = 'SunlineUKF.state'
        covarString = 'SunlineUKF.covar'

    msgSize = cssConstVehicle.getStructSize()
    inputData = cssComm.CSSArraySensorIntMsg()

    inputMessageSize = inputData.getStructSize()
    scSim.TotalSim.CreateNewMessage(simProcessName, "css_config_data",
                                          msgSize, 2, "CSSConstConfig")
    scSim.TotalSim.CreateNewMessage(simProcessName, moduleConfig.cssDataInMsgName, inputMessageSize, 2)  # number of buffers (leave at 2 as default, don't make zero)
    scSim.TotalSim.WriteMessageData("css_config_data", msgSize, 0, cssConstVehicle)

    if FilterType == 'uKF' or FilterType == 'EKF':
        scSim.AddVariableForLogging(covarString, simulationTimeStep , 0, 35)
        scSim.AddVariableForLogging(statesString, simulationTimeStep , 0, 5)
    if FilterType == 'OEKF':
        scSim.AddVariableForLogging(covarString, simulationTimeStep, 0, 8)
        scSim.AddVariableForLogging(statesString, simulationTimeStep, 0, 2)

    #
    #   initialize Simulation
    #
    scSim.InitializeSimulationAndDiscover()

    #
    #   configure a simulation stop time time and execute the simulation run
    #
    scSim.ConfigureStopTime(simulationTime)

    # Time the runs for performance comparisons
    timeStart = time.time()
    scSim.ExecuteSimulation()
    timeEnd = time.time()


    #
    #   retrieve the logged data
    #
    covarLog = scSim.GetLogVariableData(covarString)
    stateLog = scSim.GetLogVariableData(statesString)

    if FilterType == 'EKF':
        stateErrorLog = scSim.GetLogVariableData('SunlineEKF.x')
    if FilterType == 'OEKF':
        stateErrorLog = scSim.GetLogVariableData('okeefeEKF.x')
    np.set_printoptions(precision=16)

    # Get messages that will make true data
    OutSunPos = scSim.pullMessageLogData('sun_planet_data' + ".PositionVector", range(3))
    Outr_BN_N = scSim.pullMessageLogData('inertial_state_output' + ".r_BN_N", range(3))
    OutSigma_BN = scSim.pullMessageLogData('inertial_state_output' + ".sigma_BN", range(3))
    Outomega_BN = scSim.pullMessageLogData('inertial_state_output' + ".omega_BN_B", range(3))

    sHat_B = np.zeros(np.shape(OutSunPos))
    sHatDot_B = np.zeros(np.shape(OutSunPos))
    for i in range(len(OutSunPos[:,0])):
        sHat_N = (OutSunPos[i,1:] - Outr_BN_N[i,1:])/np.linalg.norm(OutSunPos[i,1:] - Outr_BN_N[i,1:])
        dcm_BN = rbk.MRP2C(OutSigma_BN[i,1:])
        sHat_B[i,0] = sHatDot_B[i,0]= OutSunPos[i,0]
        sHat_B[i,1:] = np.dot(dcm_BN, sHat_N)
        sHatDot_B[i,1:] = - np.cross(Outomega_BN[i,1:], sHat_B[i,1:] )

    expected = np.zeros(np.shape(stateLog))
    expected[:,0:4] = sHat_B
    if FilterType != 'OEKF':
        expected[:, 4:] = sHatDot_B[:,1:]

    #
    #   plot the results
    #
    if FilterType == 'EKF' or FilterType == 'OEKF':
        Fplot.StateErrorCovarPlot(stateErrorLog, covarLog, FilterType, show_plots)
    Fplot.StatesVsExpected(stateLog, covarLog, expected, FilterType, show_plots)

    if show_plots:
        plt.show()

    # close the plots being saved off to avoid over-writing old and new figures
    plt.close("all")


    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]

#
# This statement below ensures that the unit test scrip can be run as a
# stand-along python script
#
if __name__ == "__main__":
    run( True,      # show_plots
        'EKF',
         200
       )

