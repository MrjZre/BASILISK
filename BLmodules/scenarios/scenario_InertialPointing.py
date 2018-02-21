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

# Import utilities
from Basilisk.utilities import orbitalMotion, macros, unitTestSupport

# Get current file path
import sys, os, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

# Import master classes: simulation base class and scenario base class
sys.path.append(path + '/..')
from BSK_masters import BSKSim, BSKScenario

# Import plotting file for your scenario
sys.path.append(path + '/../plotting')
import BSK_Plotting as BSK_plt


# Create your own scenario child class
class scenario_InertialPointing(BSKScenario):
    def __init__(self, masterSim):
        super(scenario_InertialPointing, self).__init__(masterSim)
        self.name = 'scenario_InertialPointing'
        self.masterSim = masterSim

    def configure_initial_conditions(self):
        print '%s: configure_initial_conditions' % self.name
        # Configure FSW mode
        self.masterSim.modeRequest = 'inertial3D'
        # --Overwrite message connections as desired
        #self.masterSim.FSWModels.mrpFeedbackData.outputDataName = self.masterSim.DynModels.extForceTorqueObject.cmdTorqueInMsgName # "extTorquePntB_B_cmds"

        # Configure Dynamics initial conditions
        oe = orbitalMotion.ClassicElements()
        oe.a = 10000.0 * 1000.0  # meters
        oe.e = 0.2
        oe.i = 0.0 * macros.D2R
        oe.Omega = 0.0 * macros.D2R
        oe.omega = 0.0 * macros.D2R
        oe.f = 280.0 * macros.D2R

        mu = self.masterSim.DynModels.earthGravBody.mu
        rN, vN = orbitalMotion.elem2rv(mu, oe)
        orbitalMotion.rv2elem(mu, rN, vN)
        self.masterSim.DynModels.scObject.hub.r_CN_NInit = unitTestSupport.np2EigenVectorXd(rN)  # m   - r_CN_N
        self.masterSim.DynModels.scObject.hub.v_CN_NInit = unitTestSupport.np2EigenVectorXd(vN)  # m/s - v_CN_N
        self.masterSim.DynModels.scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]  # sigma_BN_B
        self.masterSim.DynModels.scObject.hub.omega_BN_BInit = [[0.001], [-0.01], [0.03]]  # rad/s - omega_BN_B

    def log_outputs(self):
        print '%s: log_outputs' % self.name
        samplingTime = self.masterSim.DynModels.processTasksTimeStep
        self.masterSim.TotalSim.logThisMessage(self.masterSim.DynModels.scObject.scStateOutMsgName, samplingTime)
        self.masterSim.TotalSim.logThisMessage(self.masterSim.DynModels.simpleNavObject.outputAttName, samplingTime)

        samplingTime = self.masterSim.FSWModels.processTasksTimeStep
        self.masterSim.TotalSim.logThisMessage(self.masterSim.FSWModels.trackingErrorData.outputDataName, samplingTime)
        self.masterSim.TotalSim.logThisMessage(self.masterSim.FSWModels.mrpFeedbackControlData.outputDataName, samplingTime)

    def pull_outputs(self):
        print '%s: pull_outputs' % self.name

        # Dynamics process outputs
        def print_dyn_outputs(sigma_BN, omega_BN_B):
            print 'sigma_BN = %s \n' % sigma_BN[-3:, 1:]
            print 'omega_BN_B = %s \n' % omega_BN_B[-3:, 1:]
            print 't_sim_end = %s \n' % sigma_BN[-1:, 0]
        def plot_dyn_outputs(sigma_BN, omega_BN_B):
            print "Plotting results."
            BSK_plt.plot_rotationalNav(sigma_BN, omega_BN_B)

        sigma_BN = self.masterSim.pullMessageLogData(self.masterSim.DynModels.simpleNavObject.outputAttName + ".sigma_BN", range(3))
        omega_BN_B = self.masterSim.pullMessageLogData(self.masterSim.DynModels.simpleNavObject.outputAttName + ".omega_BN_B", range(3))
        print_dyn_outputs(sigma_BN, omega_BN_B)
        plot_dyn_outputs(sigma_BN, omega_BN_B)

        # FSW process outputs
        def print_fsw_outputs(sigma_RN, sigma_BR, Lr):
            print 'sigma_RN = %s' % sigma_RN[-3:, 1:]
            print 'sigma_BR = %s' % sigma_BR[-3:, 1:]
            print 'Lr = %s' % Lr[-3:, 1:]
            print 't_sim_end = %s' % sigma_RN[-1:, 0]
        def plot_fsw_outputs(sigma_RN, sigma_BR, Lr):
            BSK_plt.plot_trackingError(sigma_BR, omega_BR_B)
            BSK_plt.plot_attitudeGuidance(sigma_RN, omega_RN_N)
            BSK_plt.plot_controlTorque(Lr)

        sigma_RN = self.masterSim.pullMessageLogData(self.masterSim.FSWModels.trackingErrorData.inputRefName + ".sigma_RN", range(3))
        omega_RN_N = self.masterSim.pullMessageLogData(self.masterSim.FSWModels.trackingErrorData.inputRefName + ".omega_RN_N", range(3))
        sigma_BR = self.masterSim.pullMessageLogData(self.masterSim.FSWModels.trackingErrorData.outputDataName + ".sigma_BR", range(3))
        omega_BR_B = self.masterSim.pullMessageLogData(self.masterSim.FSWModels.trackingErrorData.outputDataName + ".omega_BR_B", range(3))
        Lr = self.masterSim.pullMessageLogData(self.masterSim.FSWModels.mrpFeedbackControlData.outputDataName + ".torqueRequestBody", range(3))
        print_fsw_outputs(sigma_RN, sigma_BR, Lr)
        plot_fsw_outputs(sigma_RN, sigma_BR, Lr)

        # Show all plots
        BSK_plt.show_all_plots()


if __name__ == "__main__":
    # Instantiate base simulation
    TheBSKSim = BSKSim()

    # Configure an scenario in the base simulation
    TheScenario = scenario_InertialPointing(TheBSKSim)
    TheScenario.log_outputs()
    TheScenario.configure_initial_conditions()

    # Initialize simulation
    TheBSKSim.InitializeSimulationAndDiscover()

    # Configure run time and execute simulation
    simulationTime = macros.min2nano(10.)
    TheBSKSim.ConfigureStopTime(simulationTime)
    print 'Starting Execution'
    TheBSKSim.ExecuteSimulation()
    print 'Finished Execution. Post-processing results'

    # Pull the results of the base simulation running the chosen scenario
    TheScenario.pull_outputs()
