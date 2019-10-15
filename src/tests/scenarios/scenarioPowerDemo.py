''' '''
'''
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

'''
## \defgroup scenarioSimplePowerDemo
## @{
## Illustration of how to use simplePower modules to perform orbit power analysis considering attitude and orbital coupling.
#
# Simple Power System Demonstration {#scenarioPowerDemo}
# ====
#
# Scenario Description
# -----
# This scenario is intended to provide both an overview and a concrete demonstration of the features and interface of the
# simplePower group of modules, which represent Basilisk's low-fidelity power system modeling functionality. Specifically,
# simplePower modules are intended to provide three major features:
#   1. Computation of power generated by solar panels, which considers orbit and attitude dependence;
#   2. Computation of power consumed by on-board spacecraft power sinks;
#   3. Computation of the spacecraft power balance and total stored energy by the simpleBattery class.
#
# The simplePower subsystem consists of two kinds of Basilisk simModules: powerStorageBase (which is used to represent
# power storage units, and serves as the heart of the subsystem) and powerNodeBase (which is used to represent system
# components that consume or generate power). A conceptual diagram of these classes and their interfaces to eachother and the rest of Basilisk is shown in the figure below.
#  ![Simple Power System block diagram](Images/doc/simplePowerConcept.svg "Simple Power System interfaces")
#  In general, this system can be configured using the following process:
#   1. Create and configure a set of powerNodeBase modules to represent power system sources and sinks, including their nodePowerOutMsgName attributes;
#   2. Create and configure a powerStorageBase instance;
#   3. Use the addPowerNodeToModel() method from the powerStorageBase on the nodePowerOutMsgNames you configured in step 1 to link the power nodes to the powerStorageBase instance
#   4. Run the simulation.
#
#
# One version of this process is demonstrated here. A spacecraft representing a tumbling 6U cubesat is placed in a LEO orbit,
# using methods that are described in other scenarios. Three simplePower modules are created: a simpleBattery, a simpleSolarPanel,
# and a simplePowerSink (which represents the load demanded by on-board electronics.) The solar panel is assumed to be body-fixed,
# and given the parameters appropriate for a 6U cubesat. The initialization process as described above is implemented as:
# ~~~~~~~~~~~~~{.py}
#    # Create a solar panel
# solarPanel = simpleSolarPanel.SimpleSolarPanel()
# solarPanel.ModelTag = "solarPanel"
# solarPanel.stateInMsgName = scObject.scStateOutMsgName
# solarPanel.sunEclipseInMsgName = "eclipse_data_0"
# solarPanel.setPanelParameters(unitTestSupport.np2EigenVectorXd(np.array([1,0,0])), 0.06, 0.20)
# solarPanel.nodePowerOutMsgName = "panelPowerMsg"
# scenarioSim.AddModelToTask(taskName, solarPanel)
#
# #   Create a simple power sink
# powerSink = simplePowerSink.SimplePowerSink()
# powerSink.ModelTag = "powerSink2"
# powerSink.nodePowerOut = -3. # Watts
# powerSink.nodePowerOutMsgName = "powerSinkMsg"
# scenarioSim.AddModelToTask(taskName, powerSink)
#
# # Create a simpleBattery and attach the sources/sinks to it
# powerMonitor = simpleBattery.SimpleBattery()
# powerMonitor.ModelTag = "powerMonitor"
# powerMonitor.batPowerOutMsgName = "powerMonitorMsg"
# powerMonitor.storageCapacity = 10.0
# powerMonitor.storedCharge = 10.0
# powerMonitor.addPowerNodeToModel(solarPanel.nodePowerOutMsgName)
# powerMonitor.addPowerNodeToModel(powerSink.nodePowerOutMsgName)
# scenarioSim.AddModelToTask(taskName, powerMonitor)
# ~~~~~~~~~~~~~
#
# The outputs of the simplePowerSystem can be logged by calling:
# ~~~~~~~~~~~~~{.py}
# # Log the subsystem output messages at each sim timestep
# scenarioSim.TotalSim.logThisMessage(solarPanel.nodePowerOutMsgName, testProcessRate)
# scenarioSim.TotalSim.logThisMessage(powerSink.nodePowerOutMsgName, testProcessRate)
# scenarioSim.TotalSim.logThisMessage(powerMonitor.batPowerOutMsgName, testProcessRate)
#
# ...Sim Execution...
#
# # Pull the logged message attributes that we want
# supplyData = scenarioSim.pullMessageLogData(solarPanel.nodePowerOutMsgName + ".netPower_W")
# sinkData = scenarioSim.pullMessageLogData(powerSink.nodePowerOutMsgName + ".netPower_W")
# storageData = scenarioSim.pullMessageLogData(powerMonitor.batPowerOutMsgName + ".storageLevel")
# netData = scenarioSim.pullMessageLogData(powerMonitor.batPowerOutMsgName + ".currentNetPower")
# ~~~~~~~~~~~~~

# To run the scenario , call the python script through
#
#       python3 scenarioPowerDemo.py
#
# When the simulation completes, one plot is shown to demonstrate the panel's attitude and orbit dependence, the net power generated,
# the stored power, and the power consumed. An initial rise in net power from the panel facing towards the sun is cut short as the spacecraft enters eclipse;
# as it exits, the stored charge of the battery begins to rebuild.
# ![Power System Response](Images/Scenarios/powerDemo.png "Power history")
## @}
import os, inspect
import numpy as np
from matplotlib import pyplot as plt

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
bskName = 'Basilisk'
splitPath = path.split(bskName)

# Import all of the modules that we are going to be called in this simulation
from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
from Basilisk.simulation import simplePowerSink
from Basilisk.simulation import simplePowerMonitor, simpleBattery
from Basilisk.simulation import simpleSolarPanel
from Basilisk.simulation import eclipse
from Basilisk.simulation import spacecraftPlus
from Basilisk.utilities import macros
from Basilisk.utilities import orbitalMotion
from Basilisk.utilities import simIncludeGravBody
from Basilisk.utilities import astroFunctions
from Basilisk import __path__
bskPath = __path__[0]

path = os.path.dirname(os.path.abspath(__file__))

def run_scenario():
    taskName = "unitTask"               # arbitrary name (don't change)
    processname = "TestProcess"         # arbitrary name (don't change)

    # Create a sim module as an empty container
    scenarioSim = SimulationBaseClass.SimBaseClass()
    # terminateSimulation() is needed if multiple unit test scripts are run
    # that run a simulation for the test. This creates a fresh and
    # consistent simulation environment for each test run.
    scenarioSim.TotalSim.terminateSimulation()

    # Create test thread
    testProcessRate = macros.sec2nano(1.0)     # update process rate update time
    testProc = scenarioSim.CreateNewProcess(processname)
    testProc.addTask(scenarioSim.CreateNewTask(taskName, testProcessRate))

    # Create a spacecraft around Earth
    # initialize spacecraftPlus object and set properties
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "spacecraftBody"

    # clear prior gravitational body and SPICE setup definitions
    gravFactory = simIncludeGravBody.gravBodyFactory()

    planet = gravFactory.createEarth()
    planet.isCentralBody = True          # ensure this is the central gravitational body
    mu = planet.mu
    # attach gravity model to spaceCraftPlus
    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(list(gravFactory.gravBodies.values()))

    #   setup orbit using orbitalMotion library
    oe = orbitalMotion.ClassicElements()
    oe.a = astroFunctions.E_radius*1e3 + 400e3
    oe.e = 0.0
    oe.i = 0.0*macros.D2R

    oe.Omega = 0.0*macros.D2R
    oe.omega = 0.0*macros.D2R
    oe.f     = 75.0*macros.D2R
    rN, vN = orbitalMotion.elem2rv(mu, oe)

    n = np.sqrt(mu/oe.a/oe.a/oe.a)
    P = 2.*np.pi/n

    scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)
    scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)

    scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]  # sigma_BN_B
    scObject.hub.omega_BN_BInit = [[0.001], [-0.001], [0.001]]
    scenarioSim.AddModelToTask(taskName, scObject)


    #   Create an eclipse object so the panels don't always work
    eclipseObject = eclipse.Eclipse()
    eclipseObject.addPositionMsgName(scObject.scStateOutMsgName)
    eclipseObject.addPlanetName('earth')

    scenarioSim.AddModelToTask(taskName, eclipseObject)


    # setup Spice interface for some solar system bodies
    timeInitString = '2021 MAY 04 07:47:48.965 (UTC)'
    gravFactory.createSpiceInterface(bskPath + '/supportData/EphemerisData/'
                                     , timeInitString
                                     , spicePlanetNames = ["sun", "earth"]
                                     )

    scenarioSim.AddModelToTask(taskName, gravFactory.spiceObject, None, -1)


    # Create a solar panel
    solarPanel = simpleSolarPanel.SimpleSolarPanel()
    solarPanel.ModelTag = "solarPanel"
    solarPanel.stateInMsgName = scObject.scStateOutMsgName
    solarPanel.sunEclipseInMsgName = "eclipse_data_0"
    solarPanel.setPanelParameters(unitTestSupport.np2EigenVectorXd(np.array([1,0,0])), 0.2*0.3, 0.20)
    solarPanel.nodePowerOutMsgName = "panelPowerMsg"
    scenarioSim.AddModelToTask(taskName, solarPanel)

    #   Create a simple power sink
    powerSink = simplePowerSink.SimplePowerSink()
    powerSink.ModelTag = "powerSink2"
    powerSink.nodePowerOut = -3. # Watts
    powerSink.nodePowerOutMsgName = "powerSinkMsg"
    scenarioSim.AddModelToTask(taskName, powerSink)

    # Create a simpleBattery and attach the sources/sinks to it
    powerMonitor = simpleBattery.SimpleBattery()
    powerMonitor.ModelTag = "powerMonitor"
    powerMonitor.batPowerOutMsgName = "powerMonitorMsg"
    powerMonitor.storageCapacity = 10.0
    powerMonitor.storedCharge = 10.0
    powerMonitor.addPowerNodeToModel(solarPanel.nodePowerOutMsgName)
    powerMonitor.addPowerNodeToModel(powerSink.nodePowerOutMsgName)
    scenarioSim.AddModelToTask(taskName, powerMonitor)


    # Setup logging on the power system
    scenarioSim.TotalSim.logThisMessage(solarPanel.nodePowerOutMsgName, testProcessRate)
    scenarioSim.TotalSim.logThisMessage(powerSink.nodePowerOutMsgName, testProcessRate)
    scenarioSim.TotalSim.logThisMessage(powerMonitor.batPowerOutMsgName, testProcessRate)

    # Also log attitude/orbit parameters
    scenarioSim.TotalSim.logThisMessage(scObject.scStateOutMsgName, testProcessRate)
    scenarioSim.TotalSim.logThisMessage(planet.bodyInMsgName, testProcessRate)
    # Need to call the self-init and cross-init methods
    scenarioSim.InitializeSimulation()

    # Set the simulation time.
    # NOTE: the total simulation time may be longer than this value. The
    # simulation is stopped at the next logging event on or after the
    # simulation end time.
    scenarioSim.ConfigureStopTime(macros.sec2nano(P))        # seconds to stop simulation

    # Begin the simulation time run set above
    scenarioSim.ExecuteSimulation()

    # This pulls the actual data log from the simulation run.
    # Note that range(3) will provide [0, 1, 2]  Those are the elements you get from the vector (all of them)
    supplyData = scenarioSim.pullMessageLogData(solarPanel.nodePowerOutMsgName + ".netPower_W")
    sinkData = scenarioSim.pullMessageLogData(powerSink.nodePowerOutMsgName + ".netPower_W")
    storageData = scenarioSim.pullMessageLogData(powerMonitor.batPowerOutMsgName + ".storageLevel")
    netData = scenarioSim.pullMessageLogData(powerMonitor.batPowerOutMsgName + ".currentNetPower")

    scOrbit = scenarioSim.pullMessageLogData(scObject.scStateOutMsgName + ".r_BN_N", list(range(3)))
    scAtt = scenarioSim.pullMessageLogData(scObject.scStateOutMsgName+".sigma_BN", list(range(3)))

    planetOrbit = scenarioSim.pullMessageLogData(planet.bodyInMsgName+".PositionVector", list(range(3)))

    tvec = supplyData[:,0]
    tvec = tvec * macros.NANO2HOUR

    #   Plot the power states
    plt.figure()
    plt.plot(tvec,storageData[:,1],label='Stored Power (W-Hr)')
    plt.plot(tvec,netData[:,1],label='Net Power (W)')
    plt.plot(tvec,supplyData[:,1],label='Panel Power (W)')
    plt.plot(tvec,sinkData[:,1],label='Power Draw (W)')
    plt.xlabel('Time (Hr)')
    plt.ylabel('Power (W)')
    plt.grid(True)
    plt.legend()
    plt.figure()
    plt.plot(tvec, scAtt[:,1],tvec, scAtt[:,2], tvec, scAtt[:,3])

    relativeOrbit = scOrbit - planetOrbit

    plt.figure()
    plt.plot(relativeOrbit[:,1],relativeOrbit[:,2],label="Spacecraft Orbit")
    plt.arrow(0,0,planetOrbit[0,1], planetOrbit[0,2],label="Sun Direction")
    plt.title('Spacecraft Orbit')
    plt.xlabel('ECI X (m)')
    plt.ylabel('ECI Y (m)')


    plt.show()


    return



#
# This statement below ensures that the unitTestScript can be run as a
# stand-alone python script
#
if __name__ == "__main__":
    run_scenario()
