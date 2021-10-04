#
#  ISC License
#
#  Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder
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

r"""
Overview
--------

This tutorial considers a hyperbolic arrival orbit to Jupiter followed by a transfer into
a circular parking orbit around the planet. This is achieved through a single impulsive
maneuver at periapsis of the hyperbolic orbit.

The detail of the simulation script is as follows.

This script sets up a basic spacecraft which starts on a hyperbolic approach orbit to Jupiter. The simulation is
split into two chunks. The first chunk runs until the spacecraft reaches periapsis of the hyperbolic orbit. The
second chunk starts after the spacecraft performs the required maneuver and runs until the spacecraft has completed
nearly one circular revolution around Jupiter.

The desired parking orbit radius is first specified and the resulting hyperbolic arrival orbit and required delta V
is calculated. The hyperbolic time equation is used to calculate the simulation time for the first chunk.
The delta V is then added to the current spacecraft velocity at the end of the second chunk.


How to setup a basic spacecraft simulation is shown in the earlier tutorial :ref:`scenarioBasicOrbit`.
Simulating a Hohmann transfer is illustrated in :ref:`scenarioOrbitManeuver`.
Setting up multiple gravitational bodies is shown in :ref:`scenarioOrbitMultiBody`
while providing pseudo-SPICE messages is laid out in :ref:`scenarioCSS`.

This simulation combines all these techniques as well as implementing custom gravitational bodies.

The script is found in the folder ``basilisk/examples`` and executed by using::

      python3 scenarioJupiterArrival.py

Illustration of Simulation Results
----------------------------------

The following images illustrate the expected simulation run returns for a range of script configurations.

::

    show_plots = True

Plots below illustrate the scenario results for the inertial position states and Jupiter-centered arrival for the entire manueuver.

.. image:: /_images/Scenarios/scenarioJupiterArrival1.svg
   :align: center

.. image:: /_images/Scenarios/scenarioJupiterArrival2.svg
   :align: center

"""


#
# Basilisk Scenario Script and Integrated Test
#
# Purpose: Patched Conics Interplanetary Trajectory
# Author:   Leah Kiner
# Creation Date: September 4 2021
#

import os
import numpy as np


import matplotlib.pyplot as plt
from Basilisk import __path__
bskPath = __path__[0]
fileName = os.path.basename(os.path.splitext(__file__)[0])

from Basilisk.simulation import spacecraft, gravityEffector
from Basilisk.utilities import SimulationBaseClass, macros, orbitalMotion, simIncludeGravBody, unitTestSupport
from Basilisk.architecture import messaging
from Basilisk.utilities import vizSupport

def run(show_plots):
    """
    The scenarios can be run with the followings setups parameters:

    Args:
        show_plots (bool): Determines if the script should display plots
    """
    
    # Create simulation variable names
    simTaskName = "simTask"
    simProcessName = "simProcess"

    scSim = SimulationBaseClass.SimBaseClass()
    scSim.SetProgressBar(True)

    dynProcess = scSim.CreateNewProcess(simProcessName)

    # Create the dynamics task and specify the integration update time
    simulationTimeStep = macros.sec2nano(5.)

    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))

    scObject = spacecraft.Spacecraft()
    scObject.ModelTag = "spacecraftBody"

    # Create Jupiter as central body
    gravFactory = simIncludeGravBody.gravBodyFactory()
    jupiter = gravFactory.createJupiter()
    jupiter.isCentralBody = True
    scObject.gravField.setGravBodies(gravityEffector.GravBodyVector(list(gravFactory.gravBodies.values())))
    scSim.AddModelToTask(simTaskName, scObject)

    #
    # Set up A hyperbolic arrival orbit to Jupiter using the classical orbit elements
    #
    # Method:
    #
    # A circular parking orbit is desired upon arrival to Jupiter at periapsis. The parking orbit radius is chosen and
    # is used to calculate the required orbital elements for the hyperbolic orbit and delta V needed to perform at
    # periapsis.
    #
    # The circular speed of Jupiter relative to the sun (1), spacecraft circular parking speed relative to Jupiter (2),
    # spacecraft speed relative to the sun at apoapsis of the Hohmann transfer ellipse (3), spacecraft speed relative
    # to Jupiter at apoapsis of the Hohmann transfer ellipse (4), and spacecraft speed at periapsis
    # on the hyperbola before the delta V is performed are all claculated (5).
    #
    # The semimajor axis (-) of the hyperbolic orbit is calculated using the specific energy integral equation.
    # The eccentricity of the hyperbola (>1) is calculated using the combining the conic section equation at periapsis
    # with the specific energy equation and eliminating semimajor axis.
    #
    # Finally, the required delta V is calculated by subtracting the (final) desired parking orbit speed relative to Jupiter
    # from the (initial) spacecraft speed at periapsis of the hyperbola before the delta V is performed (5).
    #

    oe = orbitalMotion.ClassicElements()
    sunmu = 132600000000000000000                                               # [m^3/s^3]
    r_J_2_S = 778298361. * 1000                                                 # [m] Distance from Jupiter to Sun
    r_E_2_S = 149598023. * 1000                                                 # [m] Distance from Earth to Sun
    r_SC_J_park = 800000. * 1000                                                 # [m] Desired circular parking orbit radius
    
    V_J_C_S = np.sqrt(sunmu/r_J_2_S)                                            # [m/s] (1) "J"upiter "C"ircular speed relative to the "S"un
    V_SC_C_J = np.sqrt(jupiter.mu/r_SC_J_park)                                   # [m/s] (2) "S"pace"C"raft "C"ircular parking speed relative to "J"upiter.
    V_SC_A_S = np.sqrt( sunmu*r_E_2_S / ((r_J_2_S + r_E_2_S)*r_J_2_S) )         # [m/s] (3) "S"pace"C"raft speed at "A"poapsis of Hohmann transfer ellipse relative to the "S"un
    V_SC_A_J = V_SC_A_S - V_J_C_S                                               # [m/s] (4) "S"pace"C"raft speed at "A"poapsis of Hohmann transfer ellipse relative to "J"upiter
    
    a_H = - ( jupiter.mu / ( V_SC_A_J*V_SC_A_J) )                               # [m] Semimajor axis (-) of arrival hyperbola.
    
    V_SC_P_H = np.sqrt( (V_SC_A_J*V_SC_A_J) + (2*jupiter.mu / r_SC_J_park) )     # [m/s] (5) "S"pace"C"raft speed at "P"eriapsis of "H"ohmann transfer ellipse (Before delta V performed)
    Delta_V_Parking_Orbit = V_SC_C_J - V_SC_P_H
    print(Delta_V_Parking_Orbit)
    e_H = 1 + ((r_SC_J_park*V_SC_A_J*V_SC_A_J) / jupiter.mu)
    oe.a = a_H
    oe.e = e_H
    oe.i = 0.0 * macros.D2R
    oe.Omega = 48.2 * macros.D2R
    oe.omega = 347.8 * macros.D2R
    oe.f = 280.0 * macros.D2R
    
    # Determine required simulation time (time of flight) from SC initial position on hyperbola to periapsis. (Time until delta V must be performed)
    # Method: Use hyperbolic time equation to find TOF: (t-tp)
    zeta = 2*np.arctan( np.tan(oe.f / 2) * np.sqrt( (oe.e - 1) / (oe.e + 1) ) )
    t_tp = np.abs( np.sqrt(-oe.a * oe.a * oe.a / jupiter.mu) * ( oe.e * np.tan(zeta) - np.log( np.tan((zeta/2) + (np.pi/4)) ) ) )
    
    # Setting initial position and velocity vectors using orbital elements
    r_N, v_N = orbitalMotion.elem2rv(jupiter.mu, oe)
    oe = orbitalMotion.rv2elem(jupiter.mu, r_N, v_N)      # This stores consistent initial orbit elements
    vel_N_Earth = [0.0 * 1000, 0, 0]
    
    # Define other parking orbit parameters
    a_park = r_SC_J_park
    e_park = 0
   
    # Initialize Spacecraft States with the initialization variables
    scObject.hub.r_CN_NInit = r_N                   # [m]   = r_BN_N
    scObject.hub.v_CN_NInit = v_N                   # [m/s] = v_BN_N

    # Set the simulation time
    simulationTime = macros.sec2nano(t_tp) # Simulation Stops At Periapsis

    # Setup data logging before the simulation is initialized
    numDataPoints = 100
    samplingTime = unitTestSupport.samplingTime(simulationTime, simulationTimeStep, numDataPoints)
    dataRec = scObject.scStateOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, dataRec)

    # Vizard Visualization Option
    # ---------------------------
    # If you wish to transmit the simulation data to the United based Vizard Visualization application,
    # then uncomment the following
    # line from the python scenario script.  This will cause the BSK simulation data to
    # be stored in a binary file inside the _VizFiles sub-folder with the scenario folder.  This file can be read in by
    # Vizard and played back after running the BSK simulation.
    # To enable this, uncomment this line:

    viz = vizSupport.enableUnityVisualization(scSim, simTaskName, scObject,
                                              # saveFile=__file__,
                                              # liveStream=True,
                                              )
     
    # Initialize and excecute simulation for the first section (stops at periapsis of hyperbola before delta V)
    scSim.InitializeSimulation()
    scSim.ConfigureStopTime(simulationTime)
    scSim.ExecuteSimulation()
    
    np.set_printoptions(precision=16)
    
    # Get current spacecraft states
    posRef = scObject.dynManager.getStateObject("hubPosition")
    velRef = scObject.dynManager.getStateObject("hubVelocity")
    rN = unitTestSupport.EigenVector3d2np(posRef.getState())
    vN = unitTestSupport.EigenVector3d2np(velRef.getState())
    # print(np.linalg.norm(rN)) # Matches chosen parking orbit radius: r_SC_J_park!
    
    # Apply delta V and set new velocity state
    vHat = vN / np.linalg.norm(vN)
    vN = vN + Delta_V_Parking_Orbit*vHat
    velRef.setState(unitTestSupport.np2EigenVectorXd(vN))
    
    # Run the simulation for 2nd chunk
    scSim.ConfigureStopTime(simulationTime + macros.sec2nano(300000))
    
    scSim.ExecuteSimulation()
    
    # Pull recorded data for the entire simulation
    posData = dataRec.r_BN_N
    velData = dataRec.v_BN_N
     
    mu = jupiter.mu
    
    # Call plotting function: plotOrbits
    figureList, finalDiff = plotOrbits(dataRec.times(), posData, velData, oe, mu, jupiter, a_park, e_park)

    if show_plots:
        plt.show()

    # close the plots being saved off to avoid over-writing old and new figures
    plt.close("all")

    return finalDiff, figureList


def plotOrbits(timeAxis, posData, velData, oe, mu, jupiter, a_park, e_park):
    fileName = os.path.basename(os.path.splitext(__file__)[0])
    
    # Figure 1: Draw the inertial position vector components
    plt.close("all")  # Clears out plots from earlier test runs
    plt.figure(1)
    fig = plt.gcf()
    ax = fig.gca()
    ax.ticklabel_format(useOffset=False, style='plain')

    for idx in range(3):
        plt.plot(timeAxis * macros.NANO2SEC, posData[:,idx] / 1000.,
                 color=unitTestSupport.getLineColor(idx, 3),
                 label='$r_{BN,' + str(idx) + '}$')
    plt.legend(loc='lower right')
    plt.xlabel('Time [orbits]')
    plt.ylabel('Inertial Position [km]')
    figureList = {}
    pltName = fileName + "1"
    figureList[pltName] = plt.figure(1)
    
    # Figure 2: Plot arrival to Jupiter
    plt.figure(2,figsize=(5,5))
    plt.axis([-1500000, 1500000, -1500000, 1500000])
    # Draw the planet
    fig = plt.gcf()
    ax = fig.gca()
    ax.set_aspect('equal')
    ax.ticklabel_format(useOffset=False, style='sci')
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    planetColor = '#008800'
    planetRadius = jupiter.radEquator / 1000
    ax.add_artist(plt.Circle((0, 0), planetRadius, color=planetColor))
    # Draw the actual orbit from pulled data (DataRec)
    plt.plot(posData[:,0] / 1000., posData[:,1] / 1000., color='orangered', label='Simulated Flight')
    plt.xlabel('Jupiter Velocity Direction [km]')
    plt.ylabel('Anti-Sunward Direction [km]')
    pltName = fileName + "2"
    figureList[pltName] = plt.figure(2)
    # Draw desired parking orbit
    fData = np.linspace(0, 2*np.pi, 100)
    rData = []
    for indx in range(0, len(fData)):
        rData.append( ( a_park * (1 - e_park * e_park) ) / (1 + e_park * np.cos(fData[indx])) )
    plt.plot(rData * np.cos(fData) / 1000, rData * np.sin(fData) / 1000, '--', color='#555555', label='Desired Circ. Parking Orbit')
    plt.xlabel('Jupiter Velocity Direction [km]')
    plt.ylabel('Sunward Direction [km]')
    plt.legend(loc='upper right')
    plt.grid()
    pltName = fileName + "2"
    figureList[pltName] = plt.figure(2)
    
    finalDiff = 2
    
    return figureList, finalDiff
    
    
if __name__ == "__main__":
    run(
        True  # show_plots
        
    )

