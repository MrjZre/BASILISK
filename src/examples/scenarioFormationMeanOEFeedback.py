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

This script sets up a formation flying scenario with two spacecraft. The deputy spacecraft keeps a given
mean orbital element difference based on Lyapunov control theory.

This script is found in the folder ``src/examples`` and executed by using::

      python3 scenarioFormationMeanOEFeedback.py

The simulation layout is shown in the following illustration. Two spacecraft are orbiting the earth at
close distance. Only :math:`J_2` gravity perturbation is included. Each spacecraft sends a :ref:`simple_nav` 
output message of type :ref:`NavAttIntMsg` message at a certain period
to :ref:`meanOEFeedback`, where mean orbital element difference is calculated and necessary control force is output to
extForceTorque module.

.. image:: /_images/static/test_scenarioFormationMeanOEFeedback.svg
   :align: center

::



Illustration of Simulation Results
----------------------------------

::

    show_plots = True, useClassicElem = True

In this case, target orbital element difference is set based on classical orbital element.
This resulting feedback control error is shown below.


.. image:: /_images/Scenarios/scenarioFormationMeanOEFeedback11.svg
   :align: center

::

    show_plots = True, useClassicElem = False

In this case, target orbital element difference is set based on equinoctial orbital element.
This resulting feedback control error is shown below.

.. image:: /_images/Scenarios/scenarioFormationMeanOEFeedback20.svg
   :align: center


"""


import numpy as np
import math
import matplotlib.pyplot as plt
import os

from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import simIncludeGravBody
from Basilisk.utilities import macros
from Basilisk.utilities import orbitalMotion
from Basilisk.utilities import unitTestSupport
from Basilisk.utilities import vizSupport
from Basilisk.simulation import sim_model
from Basilisk.simulation import spacecraftPlus
from Basilisk.simulation import extForceTorque
from Basilisk.simulation import simple_nav
from Basilisk.fswAlgorithms import meanOEFeedback
from Basilisk import __path__
bskPath = __path__[0]
fileName = os.path.basename(os.path.splitext(__file__)[0])


def run(show_plots, useClassicElem, numOrbits):
    """
    At the end of the python script you can specify the following example parameters.

    Args:
        show_plots (bool): Determines if the script should display plots
        useClassicElem (bool): Determines if classic orbital element is used
    """
    scSim = SimulationBaseClass.SimBaseClass()

    # ----- dynamics ----- #
    dynProcessName = "dynProcess"
    dynTaskName = "dynTask"
    dynProcess = scSim.CreateNewProcess(dynProcessName, 2)
    dynTimeStep = macros.sec2nano(15.0)
    dynProcess.addTask(scSim.CreateNewTask(dynTaskName, dynTimeStep))

    # sc
    scObject = spacecraftPlus.SpacecraftPlus()
    scObject2 = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "scObject"
    # scObject.scStateOutMsgName = "scStateOut"
    scObject.scMassStateOutMsgName = "scMassStateOut"
    scObject2.ModelTag = "scObject2"
    scObject2.scStateOutMsgName = scObject.scStateOutMsgName + "2"
    scObject2.scMassStateOutMsgName = "scMassStateOut2"
    I = [900., 0., 0.,
         0., 800., 0.,
         0., 0., 600.]
    scObject.hub.mHub = 500.0
    scObject.hub.r_BcB_B = [[0.0], [0.0], [0.0]]
    scObject.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)
    scObject2.hub.mHub = 500.0
    scObject2.hub.r_BcB_B = [[0.0], [0.0], [0.0]]
    scObject2.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)

    scSim.AddModelToTask(dynTaskName, scObject, None, 2)
    scSim.AddModelToTask(dynTaskName, scObject2, None, 2)

    # grav
    gravFactory = simIncludeGravBody.gravBodyFactory()
    gravBodies = gravFactory.createBodies(['earth'])
    gravBodies['earth'].isCentralBody = True
    gravBodies['earth'].useSphericalHarmParams = True
    simIncludeGravBody.loadGravFromFile(
        bskPath + '/supportData/LocalGravData/GGM03S.txt', gravBodies['earth'].spherHarm, 2)
    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector(
        list(gravFactory.gravBodies.values()))
    scObject2.gravField.gravBodies = spacecraftPlus.GravBodyVector(
        list(gravFactory.gravBodies.values()))

    # extObj
    extFTObject2 = extForceTorque.ExtForceTorque()
    extFTObject2.ModelTag = "externalDisturbance2"
    extFTObject2.cmdForceInertialInMsgName = "Force_N2"
    scObject2.addDynamicEffector(extFTObject2)
    scSim.AddModelToTask(dynTaskName, extFTObject2, None, 3)

    # simple nav
    simpleNavObject = simple_nav.SimpleNav()
    simpleNavObject2 = simple_nav.SimpleNav()
    simpleNavObject.inputStateName = scObject.scStateOutMsgName
    simpleNavObject.outputTransName = "simple_trans_nav_output"
    simpleNavObject.outputAttName = "simple_att_nav_output"
    simpleNavObject2.inputStateName = scObject2.scStateOutMsgName
    simpleNavObject2.outputTransName = "simple_trans_nav_output2"
    simpleNavObject2.outputAttName = "simple_att_nav_output2"
    scSim.AddModelToTask(dynTaskName, simpleNavObject, None, 1)
    scSim.AddModelToTask(dynTaskName, simpleNavObject2, None, 1)

    # ----- fsw ----- #
    fswProcessName = "fswProcess"
    fswTaskName = "fswTask"
    fswProcess = scSim.CreateNewProcess(fswProcessName, 1)
    fswTimeStep = macros.sec2nano(15.0)
    fswProcess.addTask(scSim.CreateNewTask(fswTaskName, fswTimeStep))

    # meanOEFeedback
    meanOEFeedbackData = meanOEFeedback.meanOEFeedbackConfig()
    meanOEFeedbackWrap = scSim.setModelDataWrap(meanOEFeedbackData)
    meanOEFeedbackWrap.ModelTag = "meanOEFeedback"
    meanOEFeedbackData.chiefTransInMsgName = simpleNavObject.outputTransName
    meanOEFeedbackData.deputyTransInMsgName = simpleNavObject2.outputTransName
    meanOEFeedbackData.forceOutMsgName = extFTObject2.cmdForceInertialInMsgName
    meanOEFeedbackData.K = [1e7, 0.0, 0.0, 0.0, 0.0, 0.0,
                            0.0, 1e7, 0.0, 0.0, 0.0, 0.0,
                            0.0, 0.0, 1e7, 0.0, 0.0, 0.0,
                            0.0, 0.0, 0.0, 1e7, 0.0, 0.0,
                            0.0, 0.0, 0.0, 0.0, 1e7, 0.0,
                            0.0, 0.0, 0.0, 0.0, 0.0, 1e7]
    meanOEFeedbackData.targetDiffOeMean = [0.000, 0.000, 0.000, 0.0003, 0.0002, 0.0001]
    if useClassicElem:
        meanOEFeedbackData.oeType = 0  # 0: classic
    else:
        meanOEFeedbackData.oeType = 1  # 1: equinoctial
    meanOEFeedbackData.mu = orbitalMotion.MU_EARTH*1e9  # [m^3/s^2]
    meanOEFeedbackData.req = orbitalMotion.REQ_EARTH*1e3  # [m]
    meanOEFeedbackData.J2 = orbitalMotion.J2_EARTH      # []
    scSim.AddModelToTask(fswTaskName, meanOEFeedbackWrap, meanOEFeedbackData, 1)

    # ----- interface ----- #
    dyn2FSWInterface = sim_model.SysInterface()
    fsw2DynInterface = sim_model.SysInterface()
    dyn2FSWInterface.addNewInterface(dynProcessName, fswProcessName)
    fsw2DynInterface.addNewInterface(fswProcessName, dynProcessName)
    dynProcess.addInterfaceRef(fsw2DynInterface)
    fswProcess.addInterfaceRef(dyn2FSWInterface)

    # ----- Setup spacecraft initial states ----- #
    mu = gravFactory.gravBodies['earth'].mu
    oe = orbitalMotion.ClassicElements()
    oe.a = 11000 * 1e3  # meters
    oe.e = 0.4
    oe.i = 10.0 * macros.D2R
    oe.Omega = 00.0 * macros.D2R
    oe.omega = 70.0 * macros.D2R
    M = 0.0 * macros.D2R
    E = orbitalMotion.M2E(M, oe.e)
    oe.f = orbitalMotion.E2f(E, oe.e)
    rN, vN = orbitalMotion.elem2rv(mu, oe)
    orbitalMotion.rv2elem(mu, rN, vN)
    scObject.hub.r_CN_NInit = rN  # m
    scObject.hub.v_CN_NInit = vN  # m/s

    oe2 = orbitalMotion.ClassicElements()
    oe2.a = oe.a*(1 + 0.0001)
    oe2.e = oe.e + 0.0002
    oe2.i = oe.i - 0.0003
    oe2.Omega = oe.Omega + 0.0004
    oe2.omega = oe.omega + 0.0005
    M2 = M + 0.0006
    E2 = orbitalMotion.M2E(M2, oe.e)
    oe2.f = orbitalMotion.E2f(E2, oe.e)
    rN2, vN2 = orbitalMotion.elem2rv(mu, oe2)
    scObject2.hub.r_CN_NInit = rN2  # m
    scObject2.hub.v_CN_NInit = vN2  # m/s

    # ----- log ----- #
    orbit_period = 2*math.pi/math.sqrt(mu/oe.a**3)
    simulationTime = orbit_period*numOrbits
    simulationTime = macros.sec2nano(simulationTime)
    numDataPoints = 1000
    samplingTime = simulationTime // (numDataPoints - 1)
    scSim.TotalSim.logThisMessage(scObject.scStateOutMsgName, samplingTime)
    scSim.TotalSim.logThisMessage(scObject2.scStateOutMsgName, samplingTime)

    # if this scenario is to interface with the BSK Viz, uncomment the following lines
    # to save the BSK data to a file, uncomment the saveFile line below
    viz = vizSupport.enableUnityVisualization(scSim, dynTaskName, dynProcessName, gravBodies=gravFactory,
                                              # saveFile=fileName,
                                              scName=[scObject.ModelTag, scObject2.ModelTag])

    # ----- execute sim ----- #
    scSim.InitializeSimulationAndDiscover()
    scSim.ConfigureStopTime(simulationTime)
    scSim.ExecuteSimulation()

    # ----- pull ----- #
    pos = scSim.pullMessageLogData(scObject.scStateOutMsgName + '.r_BN_N', list(range(3)))
    vel = scSim.pullMessageLogData(scObject.scStateOutMsgName + '.v_BN_N', list(range(3)))
    pos2 = scSim.pullMessageLogData(scObject2.scStateOutMsgName + '.r_BN_N', list(range(3)))
    vel2 = scSim.pullMessageLogData(scObject2.scStateOutMsgName + '.v_BN_N', list(range(3)))
    timeData = pos[:, 0]*macros.NANO2SEC/orbit_period

    # ----- plot ----- #
    # classical oe (figure1)
    plt.figure(1)
    oed_cl = np.empty((len(pos[:, 0]), 6))
    for i in range(0, len(pos[:, 0])):
        # spacecraft 1 (chief)
        oe_cl_osc = orbitalMotion.rv2elem(mu, pos[i, 1:4], vel[i, 1:4])
        oe_cl_mean = orbitalMotion.ClassicElements()
        orbitalMotion.clMeanOscMap(orbitalMotion.REQ_EARTH*1e3, orbitalMotion.J2_EARTH, oe_cl_osc, oe_cl_mean, -1)
        # spacecraft 2 (deputy)
        oe2_cl_osc = orbitalMotion.rv2elem(mu, pos2[i, 1:4], vel2[i, 1:4])
        oe2_cl_mean = orbitalMotion.ClassicElements()
        orbitalMotion.clMeanOscMap(orbitalMotion.REQ_EARTH*1e3, orbitalMotion.J2_EARTH, oe2_cl_osc, oe2_cl_mean, -1)
        # calculate oed
        oed_cl[i, 0] = (oe2_cl_mean.a - oe_cl_mean.a)/oe_cl_mean.a  # delta a (normalized)
        oed_cl[i, 1] = oe2_cl_mean.e - oe_cl_mean.e  # delta e
        oed_cl[i, 2] = oe2_cl_mean.i - oe_cl_mean.i  # delta i
        oed_cl[i, 3] = oe2_cl_mean.Omega - oe_cl_mean.Omega  # delta Omega
        oed_cl[i, 4] = oe2_cl_mean.omega - oe_cl_mean.omega  # delta omega
        E_tmp = orbitalMotion.f2E(oe_cl_mean.f, oe_cl_mean.e)
        E2_tmp = orbitalMotion.f2E(oe2_cl_mean.f, oe2_cl_mean.e)
        oed_cl[i, 5] = orbitalMotion.E2M(
            E2_tmp, oe2_cl_mean.e) - orbitalMotion.E2M(E_tmp, oe_cl_mean.e)  # delta M
        for j in range(3, 6):
            while(oed_cl[i, j] > math.pi):
                oed_cl[i, j] = oed_cl[i, j] - 2*math.pi
            while(oed_cl[i, j] < -math.pi):
                oed_cl[i, j] = oed_cl[i, j] + 2*math.pi
    plt.plot(timeData, oed_cl[:, 0], label="da")
    plt.plot(timeData, oed_cl[:, 1], label="de")
    plt.plot(timeData, oed_cl[:, 2], label="di")
    plt.plot(timeData, oed_cl[:, 3], label="dOmega")
    plt.plot(timeData, oed_cl[:, 4], label="domega")
    plt.plot(timeData, oed_cl[:, 5], label="dM")
    plt.legend()
    plt.xlabel("time [orbit]")
    plt.ylabel("mean orbital element difference")
    figureList = {}
    pltName = fileName + "1" + str(int(useClassicElem))
    figureList[pltName] = plt.figure(1)
    # equinoctial oe (figure2)
    plt.figure(2)
    oed_eq = np.empty((len(pos[:, 0]), 6))
    for i in range(0, len(pos[:, 0])):
        # spacecraft 1 (chief)
        oe_cl_osc = orbitalMotion.rv2elem(mu, pos[i, 1:4], vel[i, 1:4])
        oe_cl_mean = orbitalMotion.ClassicElements()
        orbitalMotion.clMeanOscMap(orbitalMotion.REQ_EARTH*1e3, orbitalMotion.J2_EARTH, oe_cl_osc, oe_cl_mean, -1)
        oe_eq_mean = orbitalMotion.EquinoctialElements()
        orbitalMotion.clElem2eqElem(oe_cl_mean, oe_eq_mean)
        # spacecraft 2 (deputy)
        oe2_cl_osc = orbitalMotion.rv2elem(mu, pos2[i, 1:4], vel2[i, 1:4])
        oe2_cl_mean = orbitalMotion.ClassicElements()
        orbitalMotion.clMeanOscMap(orbitalMotion.REQ_EARTH*1e3, orbitalMotion.J2_EARTH, oe2_cl_osc, oe2_cl_mean, -1)
        oe2_eq_mean = orbitalMotion.EquinoctialElements()
        orbitalMotion.clElem2eqElem(oe2_cl_mean, oe2_eq_mean)
        # calculate oed
        oed_eq[i, 0] = (oe2_eq_mean.a - oe_eq_mean.a)/oe_eq_mean.a  # delta a (normalized)
        oed_eq[i, 1] = oe2_eq_mean.P1 - oe_eq_mean.P1  # delta P1
        oed_eq[i, 2] = oe2_eq_mean.P2 - oe_eq_mean.P2  # delta P2
        oed_eq[i, 3] = oe2_eq_mean.Q1 - oe_eq_mean.Q1  # delta Q1
        oed_eq[i, 4] = oe2_eq_mean.Q2 - oe_eq_mean.Q2  # delta Q2
        oed_eq[i, 5] = oe2_eq_mean.l - oe_eq_mean.l  # delta l
        while(oed_eq[i, 5] > math.pi):
            oed_eq[i, 5] = oed_eq[i, 5] - 2*math.pi
        while(oed_eq[i, 5] < -math.pi):
            oed_eq[i, 5] = oed_eq[i, 5] + 2*math.pi
    plt.plot(timeData, oed_eq[:, 0], label="da")
    plt.plot(timeData, oed_eq[:, 1], label="dP1")
    plt.plot(timeData, oed_eq[:, 2], label="dP2")
    plt.plot(timeData, oed_eq[:, 3], label="dQ1")
    plt.plot(timeData, oed_eq[:, 4], label="dQ2")
    plt.plot(timeData, oed_eq[:, 5], label="dl")
    plt.legend()
    plt.xlabel("time [orbit]")
    plt.ylabel("mean orbital element difference")
    pltName = fileName + "2" + str(int(useClassicElem))
    figureList[pltName] = plt.figure(2)

    if(show_plots):
        plt.show()
    plt.close("all")

    return pos, vel, pos2, vel2, numDataPoints, figureList


if __name__ == "__main__":
    run(
        True,  # show_plots
        True,  # useClassicElem
        40     # number of orbits
    )
