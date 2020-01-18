
# Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


#
# Basilisk Scenario Script and Integrated Test
#
# Purpose:  Test the gravity gradient effector module.
# Author:   Hanspeter Schaub
# Creation Date:  Jan 12, 2019
#

import sys, os, inspect
import numpy as np
import pytest



# import general simulation support files
from Basilisk.utilities import SimulationBaseClass
import matplotlib.pyplot as plt
from Basilisk.utilities import macros

# import simulation related support
from Basilisk.simulation import spacecraftPlus
from Basilisk.utilities import simIncludeGravBody, orbitalMotion, RigidBodyKinematics
from Basilisk.simulation import GravityGradientEffector
from Basilisk.utilities import unitTestSupport
#print dir(exponentialAtmosphere)
from Basilisk.simulation import dragDynamicEffector

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))


# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail(True, reason="Previously set sim parameters are not consistent with new formulation\n")

# The following 'parametrize' function decorator provides the parameters and expected results for each
#   of the multiple test runs for this test.
@pytest.mark.parametrize("outMsgType", ["default", "custom"])
@pytest.mark.parametrize("cmOffset", [[[0.1], [0.15], [-0.1]], [[0.0], [0.0], [0.0]]])


# provide a unique test method name, starting with test_
def test_gravityGradientModule(show_plots, outMsgType, cmOffset):
    """Module Unit Test"""
    # each test method requires a single assert method to be called
    [testResults, testMessage] = run(
            show_plots, outMsgType, cmOffset, 2.0)
    assert testResults < 1, testMessage


def truthGravityGradient(mu, rN, sigmaBN, hub):
    I = hub.IHubPntBc_B
    r = np.linalg.norm(rN)
    BN = RigidBodyKinematics.MRP2C(sigmaBN)
    rHatB = np.matmul(BN, rN) / r

    ggTorque = 3*mu/r/r/r * np.cross(rHatB, np.matmul(I, rHatB))

    return ggTorque

def run(show_plots, outMsgType, cmOffset, simTime):
    """Call this routine directly to run the unit test."""
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages


    # Create simulation variable names
    simTaskName = "simTask"
    simProcessName = "simProcess"

    #  Create a sim module as an empty container
    scSim = SimulationBaseClass.SimBaseClass()

    #  create the simulation process
    dynProcess = scSim.CreateNewProcess(simProcessName)

    # create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(1.0)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))
    simulationTime = macros.sec2nano(simTime)

    # create Earth Gravity Body
    gravFactory = simIncludeGravBody.gravBodyFactory()
    earth = gravFactory.createEarth()
    earth.isCentralBody = True  # ensure this is the central gravitational body
    mu = earth.mu

    # setup the orbit using classical orbit elements
    oe = orbitalMotion.ClassicElements()
    rLEO = 7000. * 1000      # meters
    oe.a = rLEO
    oe.e = 0.0001
    oe.i = 33.3 * macros.D2R
    oe.Omega = 48.2 * macros.D2R
    oe.omega = 347.8 * macros.D2R
    oe.f = 85.3 * macros.D2R
    rN, vN = orbitalMotion.elem2rv(mu, oe)
    oe = orbitalMotion.rv2elem(mu, rN, vN)      # this stores consistent initial orbit elements
                                                # with circular or equatorial orbit, some angles are arbitrary

    # setup basic spacecraftPlus module
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "bskTestSat"
    IIC = [[500., 0., 0.]
           , [0., 800., 0.]
           , [0., 0., 350.]]
    scObject.hub.r_BcB_B = cmOffset
    scObject.hub.mHub = 100.0  # kg - spacecraft mass
    scObject.hub.IHubPntBc_B = IIC
    scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)  # m   - r_BN_N
    scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)  # m/s - v_BN_N
    scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]  # sigma_BN_B
    scObject.hub.omega_BN_BInit = [[0.0], [0.0], [0.0]]  # rad/s - omega_BN_B

    scSim.AddModelToTask(simTaskName, scObject)

    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(list(gravFactory.gravBodies.values()))

    # add gravity gradient effector
    ggEff = GravityGradientEffector.GravityGradientEffector()
    ggEff.ModelTag = scObject.ModelTag
    if outMsgType == "default":
        logMsgName = ggEff.ModelTag + "_gravityGradient"
    else:
        logMsgName = "test_gravityGradient"
        ggEff.gravityGradientOutMsgName = logMsgName
    scObject.addDynamicEffector(ggEff)
    scSim.AddModelToTask(simTaskName, ggEff)

    #
    #   Setup data logging before the simulation is initialized
    #
    numDataPoints = 50
    samplingTime = simulationTime // (numDataPoints - 1)
    scSim.TotalSim.logThisMessage(scObject.scStateOutMsgName, samplingTime)
    scSim.TotalSim.logThisMessage(logMsgName, samplingTime)


    #
    #   initialize Simulation
    #
    scSim.InitializeSimulation()

    #
    #   configure a simulation stop time time and execute the simulation run
    #
    scSim.ConfigureStopTime(simulationTime)
    scSim.ExecuteSimulation()

    #
    #   retrieve the logged data
    #
    posData = scSim.pullMessageLogData(scObject.scStateOutMsgName+'.r_BN_N', list(range(3)))
    attData = scSim.pullMessageLogData(scObject.scStateOutMsgName+'.sigma_BN', list(range(3)))
    ggData = scSim.pullMessageLogData(logMsgName+'.gravityGradientTorque_B', list(range(3)))
    np.set_printoptions(precision=16)

    #
    #   plot the results
    #
    if show_plots:
        plt.close("all")  # clears out plots from earlier test runs

        # draw the inertial position vector components
        plt.close("all")  # clears out plots from earlier test runs
        plt.figure(1)
        for idx in range(1, 4):
            plt.plot(attData[:, 0] * macros.NANO2MIN, attData[:, idx],
                     color=unitTestSupport.getLineColor(idx, 3),
                     label=r'$\sigma_' + str(idx) + '$')
        plt.legend(loc='lower right')
        plt.xlabel('Time [min]')
        plt.ylabel(r'Attitude Error $\sigma_{B/R}$')

        plt.figure(2)
        for idx in range(1, 4):
            plt.plot(posData[:, 0] * macros.NANO2MIN, posData[:, idx]/1000,
                     color=unitTestSupport.getLineColor(idx, 3),
                     label=r'$r_' + str(idx) + '$')
        plt.legend(loc='lower right')
        plt.xlabel('Time [min]')
        plt.ylabel(r'Inertial Position coordinates [km]')

        plt.figure(3)
        for idx in range(1, 4):
            plt.plot(ggData[:, 0] * macros.NANO2MIN, ggData[:, idx] ,
                     color=unitTestSupport.getLineColor(idx, 3),
                     label=r'$r_' + str(idx) + '$')
        plt.legend(loc='lower right')
        plt.xlabel('Time [min]')
        plt.ylabel(r'GG Torque [Nm]')

        plt.show()
        plt.close("all")

    # compare gravity gradient torque vector to the truth
    accuracy = 1e-10
    for rV, sV, ggV in zip(posData, attData, ggData):
        ggTruth = truthGravityGradient(mu, rV[1:4], sV[1:4], scObject.hub)
        testFailCount, testMessages = unitTestSupport.compareVector(ggV[1:4],
                                                                    ggTruth,
                                                                    accuracy,
                                                                    "gravityGradientTorque_B",
                                                                    testFailCount, testMessages)


    if testFailCount == 0:
        print("PASSED: Gravity Effector" )
    else:
        print("Failed: Gravity Effector")

    return testFailCount, testMessages

    # close the plots being saved off to avoid over-writing old and new figures
if __name__ == '__main__':
    run(True,           # show_plots
        "default",      # msgOutType (default, custom)
        [[0.0], [0.0], [0.0]], # cmOffset
        3600)            # simTime (seconds)
