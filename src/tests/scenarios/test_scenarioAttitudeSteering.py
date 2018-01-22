''' '''
'''
 ISC License

 Copyright (c) 2016-2018, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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
# Purpose:  Integrated test of the spacecraftPlus(), RWs, simpleNav() and
#           MRP_Steering() modules.  Illustrates a 6-DOV spacecraft detumbling in orbit
#           while using the RWs to do the attitude control actuation.
# Author:   Hanspeter Schaub
# Creation Date:  Jan. 7, 2017
#


import pytest
import os
import inspect
import numpy as np

# import general simulation support files
from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport  # general support file with common unit test functions
import matplotlib.pyplot as plt
from Basilisk.utilities import macros

# import simulation related support
from Basilisk.simulation import spacecraftPlus
from Basilisk.utilities import simIncludeRW
from Basilisk.simulation import simple_nav
from Basilisk.simulation import reactionWheelStateEffector
from Basilisk.simulation import extForceTorque
from Basilisk.utilities import simIncludeGravBody
from Basilisk.utilities import orbitalMotion as om
from Basilisk.utilities import RigidBodyKinematics as rb

# import FSW Algorithm related support
from Basilisk.fswAlgorithms import MRP_Steering
from Basilisk.fswAlgorithms import rateServoFullNonlinear
from Basilisk.fswAlgorithms import hillPoint
from Basilisk.fswAlgorithms import attTrackingError
from Basilisk.fswAlgorithms import rwMotorTorque
from Basilisk.utilities import fswSetupRW

# import message declarations
from Basilisk.fswAlgorithms import fswMessages


# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail(True)

# The following 'parametrize' function decorator provides the parameters and expected results for each
#   of the multiple test runs for this test.
@pytest.mark.parametrize("simCase", [0, 1, 2, 3])
def test_bskAttitudeFeedbackRW(show_plots, simCase):
    '''This function is called by the py.test environment.'''
    # each test method requires a single assert method to be called
    # provide a unique test method name, starting with test_
    [testResults, testMessage] = run(True, show_plots, simCase)
    assert testResults < 1, testMessage


## \defgroup Tutorials_2_3
##   @{
## Demonstrates how to use the MRP_Steering() module to stabilize the attiude relative to the Hill Frame.
#
# Attitude Stabilization using MRP Steering and a Rate Sub-Servo System {#scenarioAttitudeSteering}
# ====
#
# Scenario Description
# -----
# This script sets up a spacecraft with 3 RWs which is orbiting the Earth.  The goal is to
# illustrate how to use the `MRP_Steering()` module with a rate sub-servo system to control
# the attitude.
#  The scenario is setup to be run in multiple configurations:
# Case  | Description
# ----- | ------------------
# 1     | Detumble with balanced gains (for inner- and outer-loop separation principle), including integral feedback
# 2     | Detumble with balanced gains (for inner- and outer-loop separation principle), without integral feedback
# 3     | Small detumble with strong steering gain violating separation principle, with \f$\omega'_{\cal B^{\ast}/R}\f$
# 4     | Small detumble with strong steering gain violating separation principle, without \f$\omega'_{\cal B^{\ast}/R}\f$
#
# The first case has a scenario that should exponentially converge to zero, while the 2nd case will only provide a bounded
# (or Lagrange stable) response.  The latter two scenarios illustrate the performance if the outer loop feedback gain
# is too strong, violating the sub-servo separation principle, and how removing a particular term in case 3 can still
# lead to a locally stable response.
#
# To run the default scenario 1., call the python script from a Terminal window through
#
#       python test_scenarioAttitudeSteering.py
#
# The simulation layout is shown in the following illustration.  A single simulation process is created
# which contains both the spacecraft simulation modules, as well as the Flight Software (FSW) algorithm
# modules.
# ![Simulation Flow Diagram](Images/doc/test_scenarioAttitudeSteering.svg "Illustration")
# The spacecraft is equipped with three RW, just as in the
# [test_scenarioAttitudeFeedbackRW.py](@ref scenarioAttitudeFeedbackRW) tutorial.  The `hillPoint()` guidance module is
# used to align the body frame \f$\cal B\f$ to the Hill frame \f$\cal H\f$.  The `rateServoFullNonlinear()` module is
# used to create the rate tracking sub-servo system.  How to setup the Hill frame guidance module is discussed in
# [test_scenarioAttitudeGuidance.py](@ref scenarioAttitudeGuidance).
#
# When the simulation completes several plots are shown for the MRP attitude history, the rate
# tracking errors, as well as the RW motor torque components, as well as the RW wheel speeds.
#
#
# The following code discusses how to setup the `MRP_Steering()` module:
# ~~~~~~~~~~~~~{.py}
#     # setup the MRP steering control module
#     mrpControlConfig = MRP_Steering.MRP_SteeringConfig()
#     mrpControlWrap = scSim.setModelDataWrap(mrpControlConfig)
#     mrpControlWrap.ModelTag = "MRP_Steering"
#
#     scSim.AddModelToTask(simTaskName, mrpControlWrap, mrpControlConfig)
#
#     mrpControlConfig.inputGuidName = attErrorConfig.outputDataName
#     mrpControlConfig.outputDataName = "rate_steering"
#     if simCase < 2:
#         mrpControlConfig.K1 = 0.05
#         mrpControlConfig.ignoreOuterLoopFeedforward = False
#     else:
#         mrpControlConfig.K1 = 2.2
#         if simCase == 2:
#             mrpControlConfig.ignoreOuterLoopFeedforward = False
#         else:
#             mrpControlConfig.ignoreOuterLoopFeedforward = True
#     mrpControlConfig.K3 = 0.75
#     mrpControlConfig.omega_max = 1. * macros.D2R
# ~~~~~~~~~~~~~
# This illustrates how to set the steering law gains, as well as the selective feedforward term inclusion.
# Details of this Steering law can be found in this
# <a target='_blank' href="http://hanspeterschaub.info/Papers/SchaubIAC2017.pdf"><b>conference paper.</b></a>
#
# The next step is to configure the rate tracking sub-servo module.
# ~~~~~~~~~~~~~~~~~{.py}
#     # setup Rate servo module
#     servoConfig = rateServoFullNonlinear.rateServoFullNonlinearConfig()
#     servoWrap = scSim.setModelDataWrap(servoConfig)
#     servoWrap.ModelTag = "rate_servo"
#
#     servoConfig.inputGuidName = attErrorConfig.outputDataName
#     servoConfig.vehConfigInMsgName = "vehicleConfigName"
#     servoConfig.rwParamsInMsgName = "rwa_config_data_parsed"
#     servoConfig.inputRWSpeedsName = rwStateEffector.OutputDataString
#     servoConfig.inputRateSteeringName = mrpControlConfig.outputDataName
#     servoConfig.outputDataName = "torque_command"
#
#     if simCase == 1:
#         servoConfig.Ki = -1
#     else:
#         servoConfig.Ki = 5.
#     servoConfig.P = 150.0
#     servoConfig.integralLimit = 2. / servoConfig.Ki * 0.1
#     servoConfig.knownTorquePntB_B = [0., 0., 0.]
#
#     scSim.AddModelToTask(simTaskName, servoWrap, servoConfig)
# ~~~~~~~~~~~~~~~~~
# The mathematical details of this paper are also found at
# <a target='_blank' href="http://hanspeterschaub.info/Papers/SchaubIAC2017.pdf"><b>conference paper</b></a>.
#
#
#
# Setup 1
# -----
#
# Which scenario is run is controlled at the bottom of the file in the code
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#        , True,        # show_plots
#        , 0            # simCase
#        )
# ~~~~~~~~~~~~~
# The first 2 arguments can be left as is.  The last arguments control the
# simulation scenario flags determines which simulation case is run.  Here an unknown external torque
# is applied, but the integral feedback term is included as well.    The
# resulting simulation illustrations are shown below.
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringSigmaBR0.svg "MRP history")
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringomegaBR0.svg "omega history")
# ![RW Motor Torque History](Images/Scenarios/test_scenarioAttitudeSteeringrwUs0.svg "RW motor torque history")
# ![RW Spin History](Images/Scenarios/test_scenarioAttitudeSteeringOmega0.svg "RW Omega history")
# Note that in the RW motor torque plot both the required control torque \f$\hat u_B\f$ and the true
# motor torque \f$u_B\f$ are shown.  This illustrates that with this maneuver the RW devices are being
# saturated, and the attitude still eventually stabilizes.
#
# Note that in this simulation setup the integral feedback term is included, and the unknown external torque
# is automatically compensated for to yield exponential convergence.  This convergence is despite having to track
# a time-varying Hill frame on an elliptic orbit.  This illustrates that all the orbital motion is propoerly
# feed-forward compensated.
#
#
# Setup 2
# -----
#
# Which scenario is run is controlled at the bottom of the file in the code
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#        , True,        # show_plots
#        , 1            # simCase
#        )
# ~~~~~~~~~~~~~
# This setup is the same as the first setup, but the integral feedback term is turned off.
# The resulting simulation illustrations are shown below.
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringSigmaBR1.svg "MRP history")
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringomegaBR1.svg "omega history")
# In this case the response, as expected, is only bounded or Lagrange stable, and does not longer converge
# due to the unmodeled external torque.
#
# Setup 3
# -----
#
# Which scenario is run is controlled at the bottom of the file in the code
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#        , True,        # show_plots
#        , 2            # simCase
#        )
# ~~~~~~~~~~~~~
# This setup investigates the small depature motion stability about the Hill frame.  Here only small initial
# attitude and rate errors are introduced.  However, the outer loop feedback gain \f$K_1\f$ is increased such that
# it violates the sub-servo loop separation principle.
# The
# resulting simulation illustrations are shown below.
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringSigmaBR2.svg "MRP history")
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringomegaBR2.svg "omega history")
# Here the local motion is now unstable, as predicted in
# <a target='_blank' href="http://hanspeterschaub.info/Papers/SchaubIAC2017.pdf"><b>conference paper</b></a>.
#
# Setup 4
# -----
#
# Which scenario is run is controlled at the bottom of the file in the code
# ~~~~~~~~~~~~~{.py}
# if __name__ == "__main__":
#     run( False,       # do unit tests
#        , True,        # show_plots
#        , 3            # simCase
#        )
# ~~~~~~~~~~~~~
# This setup also investigates the small depature motion stability about the Hill frame.  However, in this case
# the feedword term \f$\omega'_{\cal B^\ast/R}\f$ is ommited, which is predicted to yield locally stabilizing control
# similar in performance to a standard proportional-derivative or PD feedback control.
# The
# resulting simulation illustrations are shown below.
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringSigmaBR3.svg "MRP history")
# ![MRP Attitude History](Images/Scenarios/test_scenarioAttitudeSteeringomegaBR3.svg "omega history")
#
##  @}
def run(doUnitTests, show_plots, simCase):
    '''Call this routine directly to run the tutorial scenario.'''
    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty array to store test log messages

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
    simulationTime = macros.min2nano(10.)

    #
    #  create the simulation process
    #
    dynProcess = scSim.CreateNewProcess(simProcessName)

    # create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(.1)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    # if this scenario is to interface with the BSK Viz, uncomment the following lines
    # unitTestSupport.enableVisualization(scSim, dynProcess, simProcessName, 'earth')
    # The Viz only support 'earth', 'mars', or 'sun'

    #
    #   setup the simulation tasks/objects
    #

    # initialize spacecraftPlus object and set properties
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "spacecraftBody"
    # define the simulation inertia
    I = [500., 0., 0.,
         0., 300., 0.,
         0., 0., 200.]
    scObject.hub.mHub = 750.0  # kg - spacecraft mass
    scObject.hub.r_BcB_B = [[0.0], [0.0], [0.0]]  # m - position vector of body-fixed point B relative to CM
    scObject.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)
    scObject.hub.useTranslation = True
    scObject.hub.useRotation = True

    # add spacecraftPlus object to the simulation process
    scSim.AddModelToTask(simTaskName, scObject, None, 1)

    # clear prior gravitational body and SPICE setup definitions
    gravFactory = simIncludeGravBody.gravBodyFactory()

    # setup Earth Gravity Body
    earth = gravFactory.createEarth()
    earth.isCentralBody = True  # ensure this is the central gravitational body
    mu = earth.mu

    # attach gravity model to spaceCraftPlus
    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(gravFactory.gravBodies.values())

    # add RW devices
    rwFactory = simIncludeRW.rwFactory()

    # create each RW by specifying the RW type, the spin axis gsHat, plus optional arguments
    initOmega = [100.0, 200.0, 300.0]
    RW1 = rwFactory.create('Honeywell_HR16'
                           , [1, 0, 0]
                           , maxMomentum=50.
                           , Omega=initOmega[0]  # RPM
                           )
    RW2 = rwFactory.create('Honeywell_HR16'
                           , [0, 1, 0]
                           , maxMomentum=50.
                           , Omega=initOmega[1]  # RPM
                           )
    RW3 = rwFactory.create('Honeywell_HR16'
                           , [0, 0, 1]
                           , maxMomentum=50.
                           , Omega=initOmega[2]  # RPM
                           )

    numRW = rwFactory.getNumOfDevices()

    # create RW object container and tie to spacecraft object
    rwStateEffector = reactionWheelStateEffector.ReactionWheelStateEffector()
    rwFactory.addToSpacecraft("ReactionWheels", rwStateEffector, scObject)

    # add RW object array to the simulation process
    scSim.AddModelToTask(simTaskName, rwStateEffector, None, 2)

    # add the simple Navigation sensor module.  This sets the SC attitude, rate, position
    # velocity navigation message
    sNavObject = simple_nav.SimpleNav()
    sNavObject.ModelTag = "SimpleNavigation"
    scSim.AddModelToTask(simTaskName, sNavObject)

    if simCase < 2:
        extFTObject = extForceTorque.ExtForceTorque()
        extFTObject.ModelTag = "externalDisturbance"
        extFTObject.extTorquePntB_B = [[0.01], [-0.01], [0.005]]
        scObject.addDynamicEffector(extFTObject)
        scSim.AddModelToTask(simTaskName, extFTObject)

    #
    #   setup the FSW algorithm tasks
    #

    # setup guidance module
    attGuidanceConfig = hillPoint.hillPointConfig()
    attGuidanceWrap = scSim.setModelDataWrap(attGuidanceConfig)
    attGuidanceWrap.ModelTag = "hillPoint"
    attGuidanceConfig.inputNavDataName = sNavObject.outputTransName
    attGuidanceConfig.inputCelMessName = earth.bodyInMsgName
    attGuidanceConfig.outputDataName = "guidanceOut"
    scSim.AddModelToTask(simTaskName, attGuidanceWrap, attGuidanceConfig)

    # setup the attitude tracking error evaluation module
    attErrorConfig = attTrackingError.attTrackingErrorConfig()
    attErrorWrap = scSim.setModelDataWrap(attErrorConfig)
    attErrorWrap.ModelTag = "attErrorInertial3D"
    scSim.AddModelToTask(simTaskName, attErrorWrap, attErrorConfig)
    attErrorConfig.outputDataName = "attErrorInertial3DMsg"
    attErrorConfig.inputRefName = attGuidanceConfig.outputDataName
    attErrorConfig.inputNavName = sNavObject.outputAttName

    # setup the MRP steering control module
    mrpControlConfig = MRP_Steering.MRP_SteeringConfig()
    mrpControlWrap = scSim.setModelDataWrap(mrpControlConfig)
    mrpControlWrap.ModelTag = "MRP_Steering"

    scSim.AddModelToTask(simTaskName, mrpControlWrap, mrpControlConfig)

    mrpControlConfig.inputGuidName = attErrorConfig.outputDataName
    mrpControlConfig.outputDataName = "rate_steering"
    if simCase < 2:
        mrpControlConfig.K1 = 0.05
        mrpControlConfig.ignoreOuterLoopFeedforward = False
    else:
        mrpControlConfig.K1 = 2.2
        if simCase == 2:
            mrpControlConfig.ignoreOuterLoopFeedforward = False
        else:
            mrpControlConfig.ignoreOuterLoopFeedforward = True
    mrpControlConfig.K3 = 0.75
    mrpControlConfig.omega_max = 1. * macros.D2R

    # setup Rate servo module
    servoConfig = rateServoFullNonlinear.rateServoFullNonlinearConfig()
    servoWrap = scSim.setModelDataWrap(servoConfig)
    servoWrap.ModelTag = "rate_servo"

    servoConfig.inputGuidName = attErrorConfig.outputDataName
    servoConfig.vehConfigInMsgName = "vehicleConfigName"
    servoConfig.rwParamsInMsgName = "rwa_config_data_parsed"
    servoConfig.inputRWSpeedsName = rwStateEffector.OutputDataString
    servoConfig.inputRateSteeringName = mrpControlConfig.outputDataName
    servoConfig.outputDataName = "torque_command"

    if simCase == 1:
        servoConfig.Ki = -1
    else:
        servoConfig.Ki = 5.
    servoConfig.P = 150.0
    servoConfig.integralLimit = 2. / servoConfig.Ki * 0.1
    servoConfig.knownTorquePntB_B = [0., 0., 0.]

    scSim.AddModelToTask(simTaskName, servoWrap, servoConfig)

    # add module that maps the Lr control torque into the RW motor torques
    rwMotorTorqueConfig = rwMotorTorque.rwMotorTorqueConfig()
    rwMotorTorqueWrap = scSim.setModelDataWrap(rwMotorTorqueConfig)
    rwMotorTorqueWrap.ModelTag = "rwMotorTorque"
    scSim.AddModelToTask(simTaskName, rwMotorTorqueWrap, rwMotorTorqueConfig)
    # Initialize the test module msg names
    rwMotorTorqueConfig.outputDataName = rwStateEffector.InputCmds
    rwMotorTorqueConfig.inputVehControlName = servoConfig.outputDataName
    rwMotorTorqueConfig.rwParamsInMsgName = servoConfig.rwParamsInMsgName
    # Make the RW control all three body axes
    controlAxes_B = [
        1, 0, 0,
        0, 1, 0,
        0, 0, 1
    ]
    rwMotorTorqueConfig.controlAxes_B = controlAxes_B

    #
    #   Setup data logging before the simulation is initialized
    #
    numDataPoints = 200
    samplingTime = simulationTime / (numDataPoints - 1)
    scSim.TotalSim.logThisMessage(rwMotorTorqueConfig.outputDataName, samplingTime)
    scSim.TotalSim.logThisMessage(attErrorConfig.outputDataName, samplingTime)
    scSim.TotalSim.logThisMessage(sNavObject.outputTransName, samplingTime)
    scSim.TotalSim.logThisMessage(rwStateEffector.OutputDataString, samplingTime)
    scSim.TotalSim.logThisMessage(mrpControlConfig.outputDataName, samplingTime)
    rwOutName = ["rw_config_0_data", "rw_config_1_data", "rw_config_2_data"]
    for item in rwOutName:
        scSim.TotalSim.logThisMessage(item, samplingTime)

    #
    # create simulation messages
    #

    # create the FSW vehicle configuration message
    vehicleConfigOut = fswMessages.VehicleConfigFswMsg()
    vehicleConfigOut.ISCPntB_B = I  # use the same inertia in the FSW algorithm as in the simulation
    unitTestSupport.setMessage(scSim.TotalSim,
                               simProcessName,
                               servoConfig.vehConfigInMsgName,
                               vehicleConfigOut)

    # FSW RW configuration message
    # use the same RW states in the FSW algorithm as in the simulation
    fswSetupRW.clearSetup()
    for key, rw in rwFactory.rwList.iteritems():
        fswSetupRW.create(unitTestSupport.EigenVector3d2np(rw.gsHat_B), rw.Js, 0.2)
    fswSetupRW.writeConfigMessage(servoConfig.rwParamsInMsgName, scSim.TotalSim, simProcessName)

    #
    #   set initial Spacecraft States
    #
    oe = om.ClassicElements()
    oe.a = 10000000.0  # meters
    oe.e = 0.01
    oe.i = 33.3 * macros.D2R
    oe.Omega = 48.2 * macros.D2R
    oe.omega = 347.8 * macros.D2R
    oe.f = 85.3 * macros.D2R
    rN, vN = om.elem2rv(mu, oe)
    scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)  # m   - r_CN_N
    scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)  # m/s - v_CN_N
    if simCase < 2:
        scObject.hub.sigma_BNInit = [[0.5], [0.6], [-0.3]]  # sigma_CN_B
        scObject.hub.omega_BN_BInit = [[0.01], [-0.01], [-0.01]]  # rad/s - omega_CN_B
    else:
        HN = rb.euler3132C([oe.Omega, oe.i, oe.omega + oe.f])
        sBR = [0.001, 0.002, -0.003]
        BN = rb.MRP2C([0.001, 0.002, -0.003])
        BH = BN * HN
        sBN = rb.C2MRP(BH)
        scObject.hub.sigma_BNInit = [[sBN[0]], [sBN[1]], [sBN[2]]]  # sigma_CN_B
        n = np.sqrt(mu / (oe.a * oe.a * oe.a))
        scObject.hub.omega_BN_BInit = [[n * HN[2, 0]], [n * HN[2, 1]], [n * HN[2, 2]]]  # rad/s - omega_CN_B

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
    dataUsReq = scSim.pullMessageLogData(rwMotorTorqueConfig.outputDataName + ".motorTorque", range(numRW))
    dataSigmaBR = scSim.pullMessageLogData(attErrorConfig.outputDataName + ".sigma_BR", range(3))
    dataOmegaBR = scSim.pullMessageLogData(attErrorConfig.outputDataName + ".omega_BR_B", range(3))
    dataOmegaBRAst = scSim.pullMessageLogData(mrpControlConfig.outputDataName + ".omega_BastR_B", range(3))
    dataOmegaRW = scSim.pullMessageLogData(rwStateEffector.OutputDataString + ".wheelSpeeds", range(numRW))
    dataPos = scSim.pullMessageLogData(sNavObject.outputTransName + ".r_BN_N", range(3))
    dataRW = []
    for i in range(0, numRW):
        dataRW.append(scSim.pullMessageLogData(rwOutName[i] + ".u_current", range(1)))
    np.set_printoptions(precision=16)

    #
    #   plot the results
    #
    fileName = os.path.basename(os.path.splitext(__file__)[0])
    path = os.path.dirname(os.path.abspath(__file__))

    timeData = dataUsReq[:, 0] * macros.NANO2MIN
    plt.close("all")  # clears out plots from earlier test runs
    plt.figure(1)
    for idx in range(1, 4):
        plt.semilogy(timeData, np.abs(dataSigmaBR[:, idx]),
                     color=unitTestSupport.getLineColor(idx, 3),
                     label='$|\sigma_' + str(idx) + '|$')
    plt.legend(loc='upper right')
    plt.xlabel('Time [min]')
    plt.ylabel('Attitude Error $\sigma_{B/R}$')
    if doUnitTests:  # only save off the figure if doing a unit test run
        unitTestSupport.saveScenarioFigure(fileName + "SigmaBR" + str(int(simCase)), plt, path)

    plt.figure(2)
    for idx in range(1, 4):
        plt.semilogy(timeData, np.abs(dataRW[idx - 1][:, 1]),
                     color=unitTestSupport.getLineColor(idx, numRW),
                     label='$|u_{s,' + str(idx) + '}|$')
    plt.legend(loc='lower right')
    plt.xlabel('Time [min]')
    plt.ylabel('RW Motor Torque (Nm)')
    if doUnitTests:  # only save off the figure if doing a unit test run
        unitTestSupport.saveScenarioFigure(fileName + "rwUs" + str(int(simCase)), plt, path)

    plt.figure(3)
    for idx in range(1, 4):
        plt.semilogy(timeData, np.abs(dataOmegaBR[:, idx]) / macros.D2R,
                     color=unitTestSupport.getLineColor(idx, 3),
                     label='$|\omega_{BR,' + str(idx) + '}|$')
    for idx in range(1, 4):
        plt.semilogy(timeData, np.abs(dataOmegaBRAst[:, idx]) / macros.D2R,
                     '--',
                     color=unitTestSupport.getLineColor(idx, 3)
                     )
    plt.legend(loc='upper right')
    plt.xlabel('Time [min]')
    plt.ylabel('Rate Tracking Error (deg/s) ')
    if doUnitTests:  # only save off the figure if doing a unit test run
        unitTestSupport.saveScenarioFigure(fileName + "omegaBR" + str(int(simCase)), plt, path)

    plt.figure(4)
    for idx in range(1, numRW + 1):
        plt.plot(timeData, dataOmegaRW[:, idx] / macros.RPM,
                 color=unitTestSupport.getLineColor(idx, numRW),
                 label='$\Omega_{' + str(idx) + '}$')
    plt.legend(loc='upper right')
    plt.xlabel('Time [min]')
    plt.ylabel('RW Speed (RPM) ')
    if doUnitTests:  # only save off the figure if doing a unit test run
        unitTestSupport.saveScenarioFigure(fileName + "Omega" + str(int(simCase)), plt, path)

    if show_plots:
        plt.show()

    # close the plots being saved off to avoid over-writing old and new figures
    plt.close("all")

    #
    #   the python code below is for the unit testing mode.  If you are studying the scenario
    #   to learn how to run BSK, you can stop reading below this line.
    #
    if doUnitTests:
        numTruthPoints = 5
        skipValue = int(numDataPoints / numTruthPoints)
        dataUsRed = dataUsReq[::skipValue]
        dataSigmaBRRed = dataSigmaBR[::skipValue]
        dataPosRed = dataPos[::skipValue]

        # setup truth data for unit test
        truePos = [
            [-4.0203386903966456e+06, 7.4905667418525163e+06, 5.2482992115893615e+06]
            , [-4.6521134526484497e+06, 7.0418660564864147e+06, 5.3612159766829805e+06]
            , [-5.2553803148656003e+06, 6.5500098234596634e+06, 5.4412780230905702e+06]
            , [-5.8265176097709052e+06, 6.0181061406054925e+06, 5.4880726887781229e+06]
            , [-6.3621161952049593e+06, 5.4494925133885061e+06, 5.5013918238723921e+06]
        ]
        trueUs = trueSigmaBR = []

        if simCase == 0:
            trueUs = [
                [-9.3735248485571654e-01, 3.1657897125315637e-01, 9.4810829234824123e-01]
                , [4.7191187864907794e-02, -3.0070771545280692e-02, -2.9518238485616782e-02]
                , [1.7016920405413215e-02, -1.5817057493123454e-02, 1.7041006711987533e-03]
                , [1.0462152119029601e-02, -1.3835672310362663e-02, 4.7069307938441447e-03]
                , [7.9429100667987116e-03, -1.4225803320727568e-02, 5.0252369827272388e-03]
            ]
            trueSigmaBR = [
                [-7.2833461132468502e-01, 2.2697297495054194e-01, 5.0137002864322056e-01]
                , [-1.3375995332049051e-01, 2.5646319783854472e-02, 9.9894348609658193e-02]
                , [-2.6596473923292778e-02, 5.4185997488293940e-03, 2.0187273917517602e-02]
                , [-5.6260975047995720e-03, 1.1494179543533006e-03, 4.2750978169215689e-03]
                , [-1.1939254320624162e-03, 2.4393826018610445e-04, 9.0726554710592988e-04]
            ]
        if simCase == 1:
            trueUs = [
                [-9.3735248485571654e-01, 3.1657897125315637e-01, 9.4810829234824123e-01]
                , [4.7579565156181863e-02, -3.0349425236291302e-02, -3.0758207114084640e-02]
                , [1.7238526778602402e-02, -1.5954311821205262e-02, 1.6062184747321928e-03]
                , [1.0527976809083944e-02, -1.3845191318712704e-02, 4.7101442446694820e-03]
                , [7.9728496722686545e-03, -1.4219676900387224e-02, 5.0553065828725912e-03]
            ]
            trueSigmaBR = [
                [-7.2833461132468502e-01, 2.2697297495054194e-01, 5.0137002864322056e-01]
                , [-1.3680399695426440e-01, 2.4494146008974305e-02, 1.0332411551330754e-01]
                , [-2.6056558162020488e-02, 4.2029826932260149e-03, 2.1432334589966056e-02]
                , [-4.4366133145544101e-03, -2.0513208877515532e-04, 5.0642220585757807e-03]
                , [1.1719472835041103e-04, -1.1640729624930607e-03, 1.5886821146121159e-03]
            ]
        if simCase == 2:
            trueUs = [
                [5.3427982784745387e-01, 2.4950294126525017e+00, 2.5650481888590777e+00]
                , [5.4358272666288343e-04, -8.5844271924247484e-03, 1.1402708588315012e-03]
                , [2.5450020484230063e-03, 9.9162427490413693e-03, -1.4057457475478573e-03]
                , [-4.5294788639083094e-04, 2.0546056360929266e-02, 1.9900162652881723e-03]
                , [3.1307504052369151e-03, -5.2522043216498004e-02, -1.6091392647118244e-03]
            ]
            trueSigmaBR = [
                [5.9238063851049559e-03, 1.5059956700233917e-01, 1.6414145977723277e-01]
                , [-3.6813728373729475e-03, -1.2652171375839346e-03, -4.4560965458308630e-05]
                , [-3.7277213568358554e-03, 1.1091516017274978e-04, -4.6671624098081926e-06]
                , [-3.7353840579002540e-03, 1.1378091633261421e-03, 4.2064324048174655e-05]
                , [-3.6762687214375281e-03, -1.8796889549439252e-03, -6.9433492742490023e-05]
            ]
        if simCase == 3:
            trueUs = [
                [1.5463342442514050e+00, 2.4989188277446774e+00, 2.5666604392831682e+00]
                , [8.7400016892695467e-03, -2.2389585500966587e+00, -2.0172110694939094e-03]
                , [1.2942263063120260e-03, -9.0623022045545419e-04, 1.4725090860529959e-06]
                , [1.2175561336695026e-03, -9.9918509941947773e-04, 1.5678601387200759e-06]
                , [1.1342525280809703e-03, -1.0892870415896393e-03, 1.5413853915482904e-06]
            ]
            trueSigmaBR = [
                [5.9238063851049559e-03, 1.5059956700233917e-01, 1.6414145977723277e-01]
                , [1.0802870404159959e-04, -9.9707506726354513e-03, -9.5795774144360256e-05]
                , [6.3385780276990460e-08, 2.7851495444539080e-06, -4.9151262511072661e-07]
                , [3.9812854928119984e-09, 4.5312268214171323e-08, -9.7417287710713351e-09]
                , [1.0932992615194772e-10, 7.3941898989080499e-10, -1.8758847429304412e-10]
            ]

        # compare the results to the truth values
        accuracy = 1e-7

        testFailCount, testMessages = unitTestSupport.compareArray(
            trueUs, dataUsRed, accuracy, "RW us Vector",
            testFailCount, testMessages)

        testFailCount, testMessages = unitTestSupport.compareArray(
            truePos, dataPosRed, accuracy, "r_BN_N Vector",
            testFailCount, testMessages)

        testFailCount, testMessages = unitTestSupport.compareArray(
            trueSigmaBR, dataSigmaBRRed, accuracy, "sigma_BR Set",
            testFailCount, testMessages)

        #   print out success message if no error were found
        if testFailCount == 0:
            print "PASSED "
        else:
            print testFailCount
            print testMessages

    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]


#
# This statement below ensures that the unit test scrip can be run as a
# stand-along python script
#
if __name__ == "__main__":
    run(
        False,  # do unit tests
        True,  # show_plots
        0  # simCase
    )
