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
# Purpose:  Demonstrates how to setup sun heading filters
# Author:   Thibaud Teil
# Creation Date:  November 20, 2017
#



import pytest
import numpy as np

from Basilisk import __path__
bskPath = __path__[0]

from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
import matplotlib.pyplot as plt
from Basilisk.utilities import macros
from Basilisk.simulation import coarse_sun_sensor
from Basilisk.utilities import orbitalMotion as om

from Basilisk.fswAlgorithms import cssComm

from Basilisk.simulation import spacecraftPlus
from Basilisk.simulation import spice_interface
from Basilisk.fswAlgorithms import vehicleConfigData
from Basilisk.fswAlgorithms import sunlineUKF
from Basilisk.fswAlgorithms import sunlineEKF
import SunLineEKF_test_utilities as Fplot

# The following 'parametrize' function decorator provides the parameters and expected results for each
#   of the multiple test runs for this test.
@pytest.mark.parametrize("runEKF, runUKF", [
      (False, True)
    , (True, False)
])

# provide a unique test method name, starting with test_
def test_Filters(show_plots, runEKF, runUKF):
    '''This function is called by the py.test environment.'''
    # each test method requires a single assert method to be called
    [testResults, testMessage] = run( True,
            show_plots, runEKF, runUKF)
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

    filterObject.qProcVal = 0.1**2
    filterObject.qObsVal = 0.017 ** 2
    filterObject.eKFSwitch = 3. #If low (0-5), the CKF kicks in easily, if high (>10) it's mostly only EKF



## \defgroup Tutorials_4_0
##   @{
## Demonstrates how to add a Coarse Sun Sensor (CSS) sensor to a spacecraft.
#
# Coarse Sun Sensor (CSS) Simulation{#scenarioCSS}
# ====
#
# Scenario Description
# -----
# This script sets up a 6-DOF spacecraft in deep space without any gravitational bodies. Only rotational
# motion is simulated.  The script illustrates how to setup CSS sensor units and log their data.  It is possible
# to setup individual CSS sensors, or setup a constellation or array of CSS sensors.  The scenario is
# setup to be run in four different setups:
# Setup | useCSSConstellation  | usePlatform  | useEclipse | useKelly
# ----- | -------------------- | ------------ | -----------|---------
# 1     | False                | False        | False      | False
# 2     | False                | True         | False      | False
# 3     | False                | False        | True       | False
# 4     | False                | False        | False      | True
#
# To run the default scenario 1., call the python script through
#
#       python test_scenarioCSS.py
#
# When the simulation completes a plot is shown for the CSS sensor signal history.
#
# The simulation layout options (A) and (B) are shown in the following illustration.  A single simulation process is created
# which contains both the spacecraft simulation module, as well as two individual CSS sensor units.  In scenario (A)
# the CSS units are individually executed by the simulation, while scenario (B) uses a CSS constellation class
# that executes a list of CSS evaluations at the same time.
# ![Simulation Flow Diagrams](Images/doc/test_scenarioCSS.svg "Illustration")
#
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
#     scObject.hub.omega_BN_BInit = [[0.0], [0.0], [1.*macros.D2R]]   # rad/s - omega_BN_B
# ~~~~~~~~~~~~~~~~
#
# In both CSS simulation scenarios (A) and (B) the CSS modules must first be individuall created and configured.
# In this simulation each case uses two CSS sensors.  The minimum variables that must be set for each CSS
# includes:
# ~~~~~~~~~~~~~~~~{.py}
#     CSS1 = coarse_sun_sensor.CoarseSunSensor()
#     CSS1.ModelTag = "CSS1_sensor"
#     CSS1.fov = 80.*macros.D2R
#     CSS1.scaleFactor = 2.0
#     CSS1.OutputDataMsg = "CSS1_output"
#     CSS1.InputSunMsg = "sun_message"
# ~~~~~~~~~~~~~~~~
# The Field-Of-View variable fov must be specified.  This is the angle between the sensor bore-sight and
# the edge of the field of view.  Beyond this angle all sensor signals are set to zero. The
# scaleFactor variable scales a normalized CSS response to this value if facing the sun head on.
# The input message name InputSunMsg specifies an input message that contains the sun's position.
# If sensor
# corruptions are to be modeled, this can be set through the variables:
# ~~~~~~~~~~~~~~~~{.py}
#   CSS1.KellyFactor
#   CSS1.SenBias
#   CSS1.SenNoiseStd
# ~~~~~~~~~~~~~~~~
# The Kelly factor has values between 0 (off) and 1 and distorts the nominal cosine response.  The SenBias
# variable determines a normalized bias to be applied to the CSS model, and SenNoiseStd provides Gaussian noise.
#
# To create additional CSS sensor units, copies of the first CSS unit can be made.  This means only the parameters
# different in the additional units must be set.
# ~~~~~~~~~~~~~~~~{.py}
#   CSS2 = coarse_sun_sensor.CoarseSunSensor(CSS1)      # make copy of first CSS unit
#   CSS2.ModelTag = "CSS2_sensor"
#   CSS2.OutputDataMsg = "CSS2_output"
# ~~~~~~~~~~~~~~~~
#
# A key parameter that remains is the CSS sensor unit normal vector.  There are several options to set this
# vector (in body frame components).  The first method is to set \f$\hat{\mathbf n}\f$ or nHat_B directly.  This is
# done with:
# ~~~~~~~~~~~~~~~~{.py}
#   CSS1.nHat_B = [1.0, 0.0, 0.0]
#   CSS2.nHat_B = [0.0, -1.0, 0.0]
# ~~~~~~~~~~~~~~~~
# Another option is to use a frame associated relative to a common CSS platform \f$\cal P\f$.  The bundled CSS units are
# often symmetrically arranged on a platform such as in a pyramid configuration.  The the platform frame is
# specified through
# ~~~~~~~~~~~~~~~~{.py}
#   CSS1.setBodyToPlatformDCM(90.*macros.D2R, 0., 0.)
# ~~~~~~~~~~~~~~~~
# where the three orientation angles are 3-2-1 Euler angles.  These platform angles are initialized to zero.
# Next, the CSS unit direction vectors can be specified through the azimuth and elevation angles
# (\f$\phi\f$, \f$\theta\f$).  These are (3)-(-2) Euler angles.
# ~~~~~~~~~~~~~~~~{.py}
#   CSS1.phi = 90.*macros.D2R
#   CSS1.theta = 0.*macros.D2R
# ~~~~~~~~~~~~~~~~
# If no platform orientation is specified, then naturally these azimuth and elevation angles are
# measured relative to the body frame \f$\cal B\f$.
#
# An optional input message is the solar eclipse message.  If this message input name is specified for a CSS
# unit, then the eclipse information is taken into account.  If this message name is not set, then the CSS
# defaults to the spacecraft always being in the sun.
# ~~~~~~~~~~~~~~~~{.py}
#   CSS1.sunEclipseInMsgName = "eclipse_message"
# ~~~~~~~~~~~~~~~~
#
# In this scenario (A) setup the CSS unit are each evaluated separately through
# ~~~~~~~~~~~~~~~~{.py}
#   scSim.AddModelToTask(simTaskName, CSS1)
#   scSim.AddModelToTask(simTaskName, CSS2)
# ~~~~~~~~~~~~~~~~
# This means that each CSS unit creates a individual output messages.
#
# If instead a cluster of CSS units is to be evaluated as one, then the above individual CSS units
# can be grouped into a list, and added to the Basilisk execution stack as a single entity.  This is done with
# ~~~~~~~~~~~~~~~~{.py}
#   cssList = [CSS1, CSS2]
#   cssArray = coarse_sun_sensor.CSSConstellation()
#   cssArray.ModelTag = "css_array"
#   cssArray.sensorList = coarse_sun_sensor.CSSVector(cssList)
#   cssArray.outputConstellationMessage = "CSS_Array_output"
#   scSim.AddModelToTask(simTaskName, cssArray)
# ~~~~~~~~~~~~~~~~
# Here the CSSConstellation() module will call the individual CSS update functions, collect all the sensor
# signals, and store the output in a single output message containing an array of CSS sensor signals.
#
# Setup 1
# -----
#
# Which scenario is run is controlled at the bottom of the file in the code
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#          True,        # show_plots
#          False,       # useCSSConstellation
#          False,       # usePlatform
#          False,       # useEclipse
#          False        # useKelly
#        )
# ~~~~~~~~~~~~~
# The first 2 arguments can be left as is.  The remaining arguments control the
# simulation scenario flags to turn on or off certain simulation conditions.  This scenario
# simulates the CSS units being setup individually without any corruption.  The sensor unit normal
# axes are directly set, and no eclipse is modeled.  The
# resulting CSS sensor histories are shown below.
# ![CSS Sensor History](Images/Scenarios/scenarioCSS0000.svg "CSS history")
# The signals of the two CSS units range from a maximum of 2 if the CSS axis is pointing at the sun to zero.
# The limited field of view of 80 degrees causes the sensor signal to be clipped when the sun light incidence
# angle gets too small.
#
# Setup 2
# ------
#
# Here the python main function is changed to read:
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#          True,        # show_plots
#          False,       # useCSSConstellation
#          True,        # usePlatform
#          False,       # useEclipse
#          False        # useKelly
#        )
# ~~~~~~~~~~~~~
# The resulting CSS sensor signals should be identical to the first scenario as the chosen
# platform orientation and CSS azimuth and elevation angles are chosen to yield the same
# senor normal unit axes.
# ![CSS Sensor History](Images/Scenarios/scenarioCSS0100.svg "CSS history")
#
# Setup 3
# ------
#
# The 3rd scenario connects a solar eclipse message to the CSS units through:
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#          True,        # show_plots
#          False,       # useCSSConstellation
#          False,       # usePlatform
#          True,        # useEclipse
#          False        # useKelly
#        )
# ~~~~~~~~~~~~~
# The resulting CSS signals are scaled by a factor of 0.5 and are shown below.
# ![CSS Sensor History](Images/Scenarios/scenarioCSS0010.svg "CSS history")
#
# Setup 4
# ------
#
# The 4th scenario turns on Kelly corruption factor of the CSS units.
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#          True,        # show_plots
#          False,       # useCSSConstellation
#          False,       # usePlatform
#          False,       # useEclipse
#          True         # useKelly
#        )
# ~~~~~~~~~~~~~
# This causes the CSS signals to become slightly warped, and depart from the nominal cosine
# behavior.  The resulting simulation results are shown below.
# ![CSS Sensor History](Images/Scenarios/scenarioCSS0001.svg "CSS history")
#
# Setup 5
# ------
#
# The 5th scenario is identical to setup 1, but here the 2 CSS units are packaged inside the
# CSSConstellation() class.
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#          True,        # show_plots
#          True,        # useCSSConstellation
#          False,       # usePlatform
#          False,       # useEclipse
#          False        # useKelly
#        )
# ~~~~~~~~~~~~~
# The resulting simulation results are shown below to be identical to setup 1 as expected.
# ![CSS Sensor History](Images/Scenarios/scenarioCSS1000.svg "CSS history")
#

##  @}
def run(doUnitTests, show_plots, runEKF, runUKF):
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
    simulationTime = macros.sec2nano(120.)

    #
    #  create the simulation process
    #
    dynProcess = scSim.CreateNewProcess(simProcessName)

    # create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(1.)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    # if this scenario is to interface with the BSK Viz, uncomment the following lines
    # unitTestSupport.enableVisualization(scSim, dynProcess, simProcessName, 'earth')  # The Viz only support 'earth', 'mars', or 'sun'

    #
    #   setup the simulation tasks/objects
    #

    # Add the Sun

    spiceObject = spice_interface.SpiceInterface()
    spiceObject.planetNames = spice_interface.StringVector(["sun"])
    spiceObject.ModelTag = "SpiceInterfaceData"
    spiceObject.SPICEDataPath = bskPath + '/supportData/EphemerisData/'
    spiceObject.outputBufferCount = 100000
    spiceObject.UTCCalInit = '2021 MAY 04 07:47:49.965 (UTC)'

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
    totalCSSList = []
    # Initializing a 2D double array is hard with SWIG.  That's why there is this
    # layer between the above list and the actual C variables.
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
    # Initializing a 2D double array is hard with SWIG.  That's why there is this
    # layer between the above list and the actual C variables.
    for CSSHat in CSSOrientationList:
        newCSS = vehicleConfigData.CSSConfigurationElement()
        newCSS.nHat_B = CSSHat
        totalCSSList.append(newCSS)
    cssConstVehicle.nCSS = len(CSSOrientationList)
    cssConstVehicle.cssVals = totalCSSList

    msgSize = cssConstVehicle.getStructSize()
    inputData = cssComm.CSSArraySensorIntMsg()

    #
    # Setup filter
    #

    if runEKF:
        moduleConfig = sunlineEKF.sunlineEKFConfig()
        moduleWrap = scSim.setModelDataWrap(moduleConfig)
        moduleWrap.ModelTag = "SunlineEKF"
        setupEKFData(moduleConfig)

        # Add test module to runtime call list
        scSim.AddModelToTask(simTaskName, moduleWrap, moduleConfig)

        statesString = 'SunlineEKF.states'
        covarString = 'SunlineEKF.covar'
        scSim.AddVariableForLogging('SunlineEKF.x', simulationTimeStep*5, 0, 5)

    if runUKF:
        moduleConfig = sunlineUKF.SunlineUKFConfig()
        moduleWrap = scSim.setModelDataWrap(moduleConfig)
        moduleWrap.ModelTag = "SunlineUKF"
        setupUKFData(moduleConfig)

        # Add test module to runtime call list
        scSim.AddModelToTask(simTaskName, moduleWrap, moduleConfig)

        statesString = 'SunlineUKF.state'
        covarString = 'SunlineUKF.covar'

    inputMessageSize = inputData.getStructSize()
    scSim.TotalSim.CreateNewMessage(simProcessName, "css_config_data",
                                          msgSize, 2, "CSSConstConfig")
    scSim.TotalSim.CreateNewMessage(simProcessName, moduleConfig.cssDataInMsgName, inputMessageSize, 2)  # number of buffers (leave at 2 as default, don't make zero)
    scSim.TotalSim.WriteMessageData("css_config_data", msgSize, 0, cssConstVehicle)

    scSim.AddVariableForLogging(covarString, simulationTimeStep * 5, 0, 35)
    scSim.AddVariableForLogging(statesString, simulationTimeStep * 5, 0, 5)


    #
    #   initialize Simulation
    #
    scSim.InitializeSimulationAndDiscover()

    #
    #   configure a simulation stop time time and execute the simulation run
    #
    scSim.ConfigureStopTime(simulationTime)
    scSim.ExecuteSimulation()

    #
    #   retrieve the logged data
    #
    # dataCSSArray = scSim.pullMessageLogData(cssArray.outputConstellationMessage+".CosValue", range(len(cssList)))
    covarLog = scSim.GetLogVariableData(covarString)
    stateLog = scSim.GetLogVariableData(statesString)
    if runEKF:
        stateErrorLog = scSim.GetLogVariableData('SunlineEKF.x')

    np.set_printoptions(precision=16)


    #
    #   plot the results
    #
    if runEKF:
        Fplot.StateErrorCovarPlot(stateErrorLog, covarLog, show_plots)
    Fplot.StatesVsExpected(stateLog, covarLog, np.zeros(np.shape(stateLog)), show_plots)



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
    run( False,       # do unit tests
         True,      # show_plots
         True,       #EKF
         False       #UKF
       )

