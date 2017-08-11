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
#   Integrated Unit Test Script
#   Purpose:  Self-check on the AVS C-code support libraries
#   Author:  Hanspeter Schaub
#   Creation Date:  August 11, 2017
#

import pytest
import sys, os, inspect



filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('Basilisk')
sys.path.append(splitPath[0] + '/Basilisk/modules')
sys.path.append(splitPath[0] + '/Basilisk/PythonModules')

import SimulationBaseClass
import macros
# import avsSelfCheck






# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail(True)

@pytest.mark.parametrize("testRigidBodyKinematics, testOrbitalMotion, testLinearAlgebra", [
      (True, False, False)
    , (False, True, False)
    , (False, False, True)
])


# provide a unique test method name, starting with test_
def test_unitDynamicsModes(testRigidBodyKinematics, testOrbitalMotion, testLinearAlgebra):
    # each test method requires a single assert method to be called
    [testResults, testMessage] = unitAVSLibrarySelfCheck(
            testRigidBodyKinematics, testOrbitalMotion, testLinearAlgebra)
    assert testResults < 1, testMessage



def unitAVSLibrarySelfCheck(testRigidBodyKinematics, testOrbitalMotion, testLinearAlgebra):
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages
    unitTaskName = "unitTask"
    unitProcessName = "testProcess"

    scSim = SimulationBaseClass.SimBaseClass()
    scSim.TotalSim.terminateSimulation()


    #
    #  create the dynamics simulation process
    #

    dynProcess = scSim.CreateNewProcess(unitProcessName)
    # create the dynamics task and specify the integration update time
    dynProcess.addTask(scSim.CreateNewTask(unitTaskName, macros.sec2nano(0.1)))




    #
    #   initialize the simulation
    #
    scSim.InitializeSimulation()
    scSim.ConfigureStopTime(macros.sec2nano(0.001))

    #
    #   run the simulation
    #
    scSim.ExecuteSimulation()



    #   print out success message if no error were found
    if testFailCount == 0:
        print   "PASSED "

    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]

#
# This statement below ensures that the unit test scrip can be run as a
# stand-along python script
#
if __name__ == "__main__":
    unitAVSLibrarySelfCheck(
                           True,           # rigidBodyKinematics
                           False,           # orbitalMotion
                           False            # linearAlgebra
                           )

