#
#   Unit Test Script
#   Module Name:        ephemDifference
#   Creation Date:      October 16, 2018
#

from Basilisk.utilities import SimulationBaseClass, unitTestSupport, macros
from Basilisk.fswAlgorithms import ephem_difference
from Basilisk.utilities import astroFunctions


def test_ephem_difference():
    """ Test ephemDifference. """
    [testResults, testMessage] = ephemDifferenceTestFunction()
    assert testResults < 1, testMessage

def ephemDifferenceTestFunction():
    """ Test the ephemDifference module. Setup a simulation, """

    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty array to store test log messages
    unitTaskName = "unitTask"  # arbitrary name (don't change)
    unitProcessName = "TestProcess"  # arbitrary name (don't change)

    # Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()

    # This is needed if multiple unit test scripts are run
    # This create a fresh and consistent simulation environment for each test run
    unitTestSim.TotalSim.terminateSimulation()

    # Create test thread
    testProcessRate = macros.sec2nano(0.5)  # update process rate update time
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, testProcessRate))  # Add a new task to the process

    # Construct the rwNullSpace module
    # Set the names for the input messages
    moduleConfig = ephem_difference.EphemDifferenceData()  # Create a config struct
    moduleConfig.ephBaseInMsgName = "input_eph_base_name"
    moduleConfig.ephBdyCount = 3

    # This calls the algContain to setup the selfInit, crossInit, update, and reset
    moduleWrap = unitTestSim.setModelDataWrap(moduleConfig)
    moduleWrap.ModelTag = "ephemDifference"

    # Add the module to the task
    unitTestSim.AddModelToTask(unitTaskName, moduleWrap, moduleConfig)

    # Create the input message.
    inputEphemBase = ephem_difference.EphemerisIntMsg() # The clock correlation message ?
    # Get the Earth's position and velocity
    position, velocity = astroFunctions.Earth_RV(astroFunctions.JulianDate([2018, 10, 16]))
    inputEphemBase.r_BdyZero_N = position
    inputEphemBase.v_BdyZero_N = velocity
    unitTestSupport.setMessage(unitTestSim.TotalSim, unitProcessName, moduleConfig.ephBaseInMsgName, inputEphemBase)

    functions = [astroFunctions.Mars_RV, astroFunctions.Jupiter_RV, astroFunctions.Saturn_RV]

    changeBodyList = list()

    for i in range(moduleConfig.ephBdyCount):
        # Create the change body message
        changeBodyMsg = ephem_difference.EphemChangeConfig()
        changeBodyMsg.ephInMsgName = 'input_change_body_' + str(i)
        changeBodyMsg.ephOutMsgName = 'output_change_body_' + str(i)

        changeBodyList.append(changeBodyMsg)

        # Create the input message to the change body config
        inputMsg = ephem_difference.EphemerisIntMsg()
        position, velocity = functions[i](astroFunctions.JulianDate([2018, 10, 16]))
        inputMsg.r_BdyZero_N = position
        inputMsg.v_BdyZero_N = velocity

        # Set this message
        unitTestSupport.setMessage(unitTestSim.TotalSim, unitProcessName, changeBodyMsg.ephInMsgName, inputMsg)

        # Log the output message
        unitTestSim.TotalSim.logThisMessage(changeBodyMsg.ephOutMsgName, testProcessRate)

    moduleConfig.changeBodies = changeBodyList

    # unitTestSim.TotalSim.logThisMessage(moduleConfig.outputNavName, testProcessRate)

    # Initialize the simulation
    unitTestSim.InitializeSimulation()

    # The result isn't going to change with more time. The module will continue to produce the same result
    unitTestSim.ConfigureStopTime(0)  # seconds to stop simulation
    unitTestSim.ExecuteSimulation()

    trueRVector = [[69313607.6209608,  -75620898.04028425,   -5443274.17030424],
                   [-5.33462105e+08,  -7.56888610e+08,   1.17556184e+07],
                   [9.94135029e+07,  -1.54721593e+09,   1.65081472e+07]]

    trueVVector = [[15.04232523,  -1.13359121,   0.47668898],
                   [23.2531093,  -33.17628299,  -0.22550391],
                   [21.02793499, -25.86425597,  -0.38273815]]

    posAcc = 1e1
    velAcc = 1e-4

    for i in range(moduleConfig.ephBdyCount):

        outputData_R = unitTestSim.pullMessageLogData('output_change_body_' + str(i) + '.r_BdyZero_N', range(3))
        outputData_V = unitTestSim.pullMessageLogData('output_change_body_' + str(i) + '.v_BdyZero_N', range(3))
        # print(outputData_R)
        # print(outputData_V)

        # At each timestep, make sure the vehicleConfig values haven't changed from the initial values
        testFailCount, testMessages = unitTestSupport.compareArrayND([trueRVector[i]], outputData_R,
                                                                     posAcc,
                                                                     "ephemDifference position output body " + str(i),
                                                                     2, testFailCount, testMessages)
        testFailCount, testMessages = unitTestSupport.compareArrayND([trueVVector[i]], outputData_V,
                                                                     velAcc,
                                                                     "ephemDifference velocity output body " + str(i),
                                                                     2, testFailCount, testMessages)

    if testFailCount == 0:
        print("Passed")

    return [testFailCount, ''.join(testMessages)]

if __name__ == '__main__':
    test_ephem_difference()