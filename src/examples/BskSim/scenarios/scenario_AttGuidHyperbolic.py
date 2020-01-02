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

"""
Overview
--------

This script sets up a 6-DOF spacecraft on a hyperbolic trajectory. The goal of this tutorial is to demonstrate how to
configure a velocity pointing FSW in the new BSK_Sim architecture.

The script is found in the folder ``src/examples/BskSim/scenarios`` and executed by using::

      python3 scenario_AttGuidHyperbolic.py


The simulation mimics the basic simulation simulation in the earlier tutorial in
:ref:`scenarioAttGuideHyperbolic.

The simulation layout is shown in the following illustration.

.. image:: /_images/static/test_scenario_AttGuidHyperbolic.svg
   :align: center


Custom Dynamics Configurations Instructions
-------------------------------------------

The modules required for this scenario are identical to those used in :ref:`scenario_AttGuidance`.

Custom FSW Configurations Instructions
--------------------------------------

The only new module required to configure the "velocityPoint" FSW mode is ``velocityPoint`` itself.
Unlike hill pointing, this module provides a pointing model relative to the velocity vector.

The advantage of the BSK_Sim architecture becomes apparent here. All modules and setup required for the MRP Feedback task
were already defined from an earlier scenario. The user simply adds the preconfigured task to the event without
having to manually reconfigure the messages. Now there is an additional FSW mode available for all current and
future :ref:`BskSim` files.

Illustration of Simulation Results
----------------------------------

::

    showPlots = True

.. image:: /_images/Scenarios/scenario_AttGuidHyperbolic_attitudeErrorNorm.svg
   :align: center

.. image:: /_images/Scenarios/scenario_AttGuidHyperbolic_rwMotorTorque.svg
   :align: center

.. image:: /_images/Scenarios/scenario_AttGuidHyperbolic_rateError.svg
   :align: center

.. image:: /_images/Scenarios/scenario_AttGuidHyperbolic_orbit.svg
   :align: center

"""


# Import utilities
from Basilisk.utilities import orbitalMotion, macros, unitTestSupport, vizSupport

# Get current file path
import sys, os, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

# Import master classes: simulation base class and scenario base class
sys.path.append(path + '/..')
from BSK_masters import BSKSim, BSKScenario

# Import plotting files for your scenario
sys.path.append(path + '/../plotting')
import BSK_Plotting as BSK_plt
import BSK_Dynamics, BSK_Fsw

sys.path.append(path + '/../../')
import scenarioAttGuideHyperbolic as scene_plt


# Create your own scenario child class
class scenario_VelocityPointing(BSKSim, BSKScenario):
    def __init__(self):
        super(scenario_VelocityPointing, self).__init__()
        self.name = 'scenario_VelocityPointing'

        self.set_DynModel(BSK_Dynamics)
        self.set_FswModel(BSK_Fsw)
        self.initInterfaces()

        self.configure_initial_conditions()
        self.log_outputs()

        # if this scenario is to interface with the BSK Viz, uncomment the following line
        # vizSupport.enableUnityVisualization(self, self.DynModels.taskName, self.DynamicsProcessName,
        #                                     gravBodies=self.DynModels.gravFactory,
        #                                     saveFile=filename)

    def configure_initial_conditions(self):
        print('%s: configure_initial_conditions' % self.name)
        # Configure FSW mode
        self.modeRequest = 'velocityPoint'

        # Configure Dynamics initial conditions
        oe = orbitalMotion.ClassicElements()
        oe.a = -150000.0 * 1000  # meters
        oe.e = 1.5
        oe.i = 33.3 * macros.D2R
        oe.Omega = 48.2 * macros.D2R
        oe.omega = 347.8 * macros.D2R
        oe.f = 30 * macros.D2R
        mu = self.get_DynModel().gravFactory.gravBodies['earth'].mu
        rN, vN = orbitalMotion.elem2rv(mu, oe)
        self.get_DynModel().scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)  # m   - r_CN_N
        self.get_DynModel().scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)  # m/s - v_CN_N
        self.get_DynModel().scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]  # sigma_BN_B
        self.get_DynModel().scObject.hub.omega_BN_BInit = [[0.001], [-0.01], [0.03]]  # rad/s - omega_BN_B

        # Safe orbit elements for postprocessing
        self.oe = oe


    def log_outputs(self):
        print('%s: log_outputs' % self.name)
        # Dynamics process outputs
        samplingTime = self.get_DynModel().processTasksTimeStep
        self.TotalSim.logThisMessage(self.get_DynModel().simpleNavObject.outputAttName, samplingTime)
        self.TotalSim.logThisMessage(self.get_DynModel().simpleNavObject.outputTransName, samplingTime)

        # FSW process outputs
        samplingTime = self.get_FswModel().processTasksTimeStep
        self.TotalSim.logThisMessage(self.get_FswModel().trackingErrorData.outputDataName, samplingTime)
        self.TotalSim.logThisMessage(self.get_FswModel().mrpFeedbackRWsData.outputDataName, samplingTime)

    def pull_outputs(self, showPlots):
        print('%s: pull_outputs' % self.name)
        # Dynamics process outputs
        r_BN_N = self.pullMessageLogData(self.get_DynModel().simpleNavObject.outputTransName + ".r_BN_N", list(range(3)))
        v_BN_N = self.pullMessageLogData(self.get_DynModel().simpleNavObject.outputTransName + ".v_BN_N", list(range(3)))

        # FSW process outputs
        sigma_BR = self.pullMessageLogData(self.get_FswModel().trackingErrorData.outputDataName + ".sigma_BR", list(range(3)))
        omega_BR_B = self.pullMessageLogData(self.get_FswModel().trackingErrorData.outputDataName + ".omega_BR_B", list(range(3)))
        Lr = self.pullMessageLogData(self.get_FswModel().mrpFeedbackRWsData.outputDataName + ".torqueRequestBody", list(range(3)))

        # Plot results
        BSK_plt.clear_all_plots()
        timeLineSet = sigma_BR[:, 0] * macros.NANO2MIN
        scene_plt.plot_track_error_norm(timeLineSet, sigma_BR)
        scene_plt.plot_control_torque(timeLineSet, Lr)
        scene_plt.plot_rate_error(timeLineSet, omega_BR_B)
        scene_plt.plot_orbit(self.oe,
                             self.get_DynModel().gravFactory.gravBodies['earth'].mu,
                             self.get_DynModel().gravFactory.gravBodies['earth'].radEquator,
                             r_BN_N, v_BN_N)
        figureList = {}
        if showPlots:
            BSK_plt.show_all_plots()
        else:
            fileName = os.path.basename(os.path.splitext(__file__)[0])
            figureNames = ["attitudeErrorNorm", "rwMotorTorque", "rateError", "orbit"]
            figureList = BSK_plt.save_all_plots(fileName, figureNames)

        return figureList


def runScenario(TheScenario):
    # Initialize simulation
    TheScenario.InitializeSimulationAndDiscover()

    # Configure run time and execute simulation
    simulationTime = macros.min2nano(10.)
    TheScenario.ConfigureStopTime(simulationTime)
    print('BSKSim: Starting Execution')
    TheScenario.ExecuteSimulation()
    print('BSKSim: Finished Execution. Post-processing results')

def run(showPlots):
    """
       The scenarios can be run with the followings setups parameters:

       Args:
           showPlots (bool): Determines if the script should display plots

    """
    # Instantiate base simulation

    # Configure a scenario in the base simulation
    TheScenario = scenario_VelocityPointing()
    runScenario(TheScenario)
    figureList = TheScenario.pull_outputs(showPlots)

    return figureList

if __name__ == "__main__":
    run(True)
