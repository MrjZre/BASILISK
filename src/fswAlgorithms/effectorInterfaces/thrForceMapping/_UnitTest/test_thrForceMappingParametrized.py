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
#
#   Unit Test Script
#   Module Name:        thrForceMapping
#   Author:             Hanspeter Schaub
#   Creation Date:      July 4, 2016
#

import pytest






# Import all of the modules that we are going to be called in this simulation
from Basilisk.utilities import SimulationBaseClass
from Basilisk.simulation import alg_contain
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
import matplotlib.pyplot as plt
from Basilisk.fswAlgorithms import thrForceMapping
from Basilisk.utilities import macros
from Basilisk.utilities import fswSetupThrusters
from Basilisk.simulation import simFswInterfaceMessages



import os, inspect
import numpy as np

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

def results_computeAngErr(D, BLr_B, F, thrForceMag, numThrusters):
    returnAngle = 0.0
    DT = np.transpose(D)

    if np.linalg.norm(BLr_B) > 10**-9:
        tauActual_B = [0.0, 0.0, 0.0]
        BLr_B_hat = BLr_B/np.linalg.norm(BLr_B)
        for i in range(0, numThrusters):

            if thrForceMag[i] <= 0.0:
                continue
            else:
                if abs(F[i]) < thrForceMag[i]:
                    thrForce = F[i]
                else:
                    thrForce = thrForceMag[i]*abs(F[i])/F[i]

            LrEffector_B = thrForce*DT[i,:]
            tauActual_B += LrEffector_B

        tauActual_B = tauActual_B/np.linalg.norm(tauActual_B)

        if np.dot(BLr_B_hat, tauActual_B) < 1.0:
            returnAngle = np.arccos(np.dot(BLr_B_hat, tauActual_B))

    return returnAngle


def mapToForce(D, Lr_Bar):
    DT = np.transpose(D)
    DDT = np.matmul(D, DT)
    if np.linalg.det(DDT) < 0.0005:
        for i in range(0, len(DDT)):
            if DDT[i][i] == 0.0:
                DDT[i][i] = 1.0
    DDTInv = np.linalg.inv(DDT)
    DDTInvLr_Bar = np.dot(DDTInv, Lr_Bar)
    F = np.dot(DT, DDTInvLr_Bar)
    return F

def results_thrForceMapping(Lr, COrig, COM, rData, gData, thrForceSign, thrForceMag, angErrThresh, numThrusters):

    # Produce the forces with all thrusters included
    # thrForceMag = [thrForceMag]*len(gData)
    rData = np.array(rData)
    gData = np.array(gData)
    Lr = np.array(Lr)
    C = np.array(COrig)
    C = np.reshape(C, ((len(C)/3), 3), 'C')
    CT = np.transpose(C)
    Lr_Bar = np.dot(CT,np.dot(C,Lr))
    Lr_offset = [0.0, 0.0, 0.0]
    # Compute D Matrix and Determine Force
    D = np.zeros((3,len(rData)))
    for i in range(len(rData)):
        if thrForceMag[i] <= 0:
            continue
        else:
            D[:,i] = np.cross((rData[i,:] - COM), gData[i,:])
        if(thrForceSign < 0):
          Lr_offset -= thrForceMag[i]*np.cross((rData[i,:] - COM), gData[i,:])
    Lr_Bar = Lr_Bar + Lr_offset
    F = mapToForce(D, Lr_Bar)

    # Subtract off minimum force (remove null space contribution)
    if thrForceSign > 0:
        F[0:numThrusters] = F[0:numThrusters] - min(F[0:numThrusters])

    # Identify any negative forces
    t = (F[:]*thrForceSign > 0.0005)

    # Recompute the D Matrix with negative forces removed and compute Force
    # We currently don't have the availability message in place yet
    numAvailThrusters = numThrusters

    if numAvailThrusters is not numThrusters or thrForceSign < 0:
        DNew = np.array([])
        for i in range(0,len(F)):
            if t[i]:
                DNew = np.append(DNew, np.cross((rData[i,:] - COM), gData[i]))
        DNew = np.reshape(DNew, (3, (len(DNew) / 3)), 'F')
        FNew = mapToForce(DNew, Lr_Bar)

        # Remove minumum force
        if thrForceSign > 0:
            FNew[0:numThrusters] = FNew[0:numThrusters] - min(FNew[0:numThrusters])

        count = 0
        for i in range(0,len(F)):
            if t[i]:
                F[i] = FNew[count]
                count += 1
            else:
                F[i] = 0.0


    angle = results_computeAngErr(D, Lr_Bar, F, thrForceMag, numThrusters)

    if angle > angErrThresh:

        maxFractUse = 0.0
        for i in range(0, numThrusters):
            if thrForceMag[i] > 0 and abs(F[i])/thrForceMag[i] > maxFractUse:
                maxFractUse = abs(F[i])/thrForceMag[i]
        if maxFractUse > 1.0:
            F = F/maxFractUse

    return F

# Uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed.
# @pytest.mark.skipif(conditionstring)
# Uncomment this line if this test has an expected failure, adjust message as needed.
# @pytest.mark.xfail(conditionstring)
# Provide a unique test method name, starting with 'test_'.
# The following 'parametrize' function decorator provides the parameters and expected results for each
#   of the multiple test runs for this test.

@pytest.mark.parametrize("useDVThruster", [True, False])
@pytest.mark.parametrize("useCOMOffset", [True, False])
@pytest.mark.parametrize("dropThruster", [True, False])
@pytest.mark.parametrize("dropAxis", [True, False])
@pytest.mark.parametrize("saturateThrusters", [0, 1, 2])
@pytest.mark.parametrize("misconfigThruster", [True, False])


# update "module" in this function name to reflect the module name
def test_module(show_plots, useDVThruster, useCOMOffset, dropThruster, dropAxis, saturateThrusters, misconfigThruster):
    # each test method requires a single assert method to be called
    [testResults, testMessage] = thrusterForceTest(show_plots, useDVThruster, useCOMOffset, dropThruster,
                                                   dropAxis, saturateThrusters, misconfigThruster)
    assert testResults < 1, testMessage


def thrusterForceTest(show_plots, useDVThruster, useCOMOffset, dropThruster, dropAxis, saturateThrusters, misconfigThruster):
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages
    unitTaskName = "unitTask"               # arbitrary name (don't change)
    unitProcessName = "TestProcess"         # arbitrary name (don't change)

    # Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()
    # terminateSimulation() is needed if multiple unit test scripts are run
    # that run a simulation for the test. This creates a fresh and
    # consistent simulation environment for each test run.
    unitTestSim.TotalSim.terminateSimulation()

    # Create test thread
    testProcessRate = macros.sec2nano(0.5)     # update process rate update time
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, testProcessRate))


    # Construct algorithm and associated C++ container
    moduleConfig = thrForceMapping.thrForceMappingConfig()
    moduleWrap = unitTestSim.setModelDataWrap(moduleConfig)
    moduleWrap.ModelTag = "thrForceMapping"


    # Add test module to runtime call list
    unitTestSim.AddModelToTask(unitTaskName, moduleWrap, moduleConfig)

    # Initialize the test module configuration data
    moduleConfig.inputVehControlName = "LrRequested"
    moduleConfig.inputThrusterConfName = "RCSThrusters"
    moduleConfig.outputDataName = "thrusterForceOut"
    moduleConfig.inputVehicleConfigDataName = "vehicleConfigName"

    # write vehicle configuration message
    vehicleConfigOut = thrForceMapping.VehicleConfigFswMsg()
    inputMessageSize = vehicleConfigOut.getStructSize()
    unitTestSim.TotalSim.CreateNewMessage(unitProcessName,
                                          moduleConfig.inputVehicleConfigDataName,
                                          inputMessageSize,
                                          2)  # number of buffers (leave at 2 as default, don't make zero)
    if useCOMOffset == 1:
        CoM_B = [0,0,0.02]
    else:
        CoM_B = [0,0,0]
    vehicleConfigOut.CoM_B = CoM_B
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.inputVehicleConfigDataName,
                                          inputMessageSize,
                                          0,
                                          vehicleConfigOut)

    # Create input message and size it because the regular creator of that message
    # is not part of the test.
    inputMessageData = thrForceMapping.CmdTorqueBodyIntMsg()  # Create a structure for the input message
    inputMessageSize = inputMessageData.getStructSize()                           # 3 doubles
    unitTestSim.TotalSim.CreateNewMessage(unitProcessName,
                                          moduleConfig.inputVehControlName,
                                          inputMessageSize,
                                          2)            # number of buffers (leave at 2 as default, don't make zero)

    requestedTorque = [1.0, -0.5, 0.7]              # Set up a list as a 3-vector
    if saturateThrusters>0:        # default angErrThresh is 0, thus this should trigger scaling
        requestedTorque = [10.0, -5.0, 7.0]
    if saturateThrusters==2:        # angle is set and small enough to trigger scaling
        moduleConfig.angErrThresh = 10.0*macros.D2R
    if saturateThrusters==3:        # angle is too large enough to trigger scaling
        moduleConfig.angErrThresh = 40.0*macros.D2R

    inputMessageData.torqueRequestBody = requestedTorque   # write torque request to input message
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.inputVehControlName,
                                          inputMessageSize,
                                          0,
                                          inputMessageData)             # write data into the simulator

    moduleConfig.epsilon = 0.0005
    fswSetupThrusters.clearSetup()
    MAX_EFF_CNT = simFswInterfaceMessages.MAX_EFF_CNT
    rcsLocationData = np.zeros((MAX_EFF_CNT, 3))
    rcsDirectionData = np.zeros((MAX_EFF_CNT, 3))

    if useDVThruster:
        # DV thruster setup
        moduleConfig.thrForceSign = -1
        moduleConfig.controlAxes_B = [
              1, 0, 0
            , 0, 1, 0
        ]
        if dropThruster:
            numThrusters = 4
            rcsLocationData[0:4] = [ \
            [0.35766849176297305, 0.20650000000000013, -0.1671],
            [0.3576684917629732, -0.20649999999999988, -0.1671],
            [-0.35766849176297305, -0.20650000000000018, -0.1671],
            [-0.35766849176297333, 0.20649999999999968, -0.1671] \
                    ]
            rcsDirectionData[0:4] = [ \
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0] \
                ]
        else:
            numThrusters = 6
            rcsLocationData[0:6] = [ \
                [0, 0.413, -0.1671],
                [0.35766849176297305, 0.20650000000000013, -0.1671],
                [0.3576684917629732, -0.20649999999999988, -0.1671],
                [0, -0.413, -0.1671],
                [-0.35766849176297305, -0.20650000000000018, -0.1671],
                [-0.35766849176297333, 0.20649999999999968, -0.1671] \
                ]
            rcsDirectionData[0:6] = [ \
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0] \
                ]

    else:
        # RCS thruster setup
        moduleConfig.thrForceSign = +1
        if dropAxis:
            moduleConfig.controlAxes_B = [
                1, 0, 0
                , 0, 0, 1
            ]
        else:
            moduleConfig.controlAxes_B = [
                  1, 0, 0
                , 0, 1, 0
                , 0, 0, 1
            ]
        if dropThruster:
            numThrusters = 7
            rcsLocationData[0:7] = [ \
                [-0.86360, -0.82550, 1.79070],
                [-0.82550, -0.86360, 1.79070],
                [0.82550, 0.86360, 1.79070],
                [0.86360, 0.82550, 1.79070],
                [-0.86360, -0.82550, -1.79070],
                [-0.82550, -0.86360, -1.79070],
                [0.82550, 0.86360, -1.79070] \
                ]
            rcsDirectionData[0:7] = [ \
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
                [-1.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0] \
                ]
        else:
            numThrusters = 8
            rcsLocationData[0:8] = [ \
                [-0.86360, -0.82550, 1.79070],
                [-0.82550, -0.86360, 1.79070],
                [0.82550, 0.86360, 1.79070],
                [0.86360, 0.82550, 1.79070],
                [-0.86360, -0.82550, -1.79070],
                [-0.82550, -0.86360, -1.79070],
                [0.82550, 0.86360, -1.79070],
                [0.86360, 0.82550, -1.79070] \
                ]
            rcsDirectionData[0:8] = [ \
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
                [-1.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
                [-1.0, 0.0, 0.0] \
                ]

    maxThrust = 0.95
    if useDVThruster:
        maxThrust = 10.0





    for i in range(numThrusters):
        if misconfigThruster and i == 0:
            maxThrustConfig = 0.0
        else:
            maxThrustConfig = maxThrust
        fswSetupThrusters.create(rcsLocationData[i], rcsDirectionData[i], maxThrustConfig)
    fswSetupThrusters.writeConfigMessage(  moduleConfig.inputThrusterConfName,
                                           unitTestSim.TotalSim,
                                           unitProcessName)

    # Setup logging on the test module output message so that we get all the writes to it
    unitTestSim.TotalSim.logThisMessage(moduleConfig.outputDataName, testProcessRate)

    # Need to call the self-init and cross-init methods
    unitTestSim.InitializeSimulation()

    # Set the simulation time.
    # NOTE: the total simulation time may be longer than this value. The
    # simulation is stopped at the next logging event on or after the
    # simulation end time.
    unitTestSim.ConfigureStopTime(macros.sec2nano(0.5))        # seconds to stop simulation

    # Begin the simulation time run set above
    unitTestSim.ExecuteSimulation()

    # This pulls the actual data log from the simulation run.
    # Note that range(3) will provide [0, 1, 2]  Those are the elements you get from the vector (all of them)
    moduleOutputName = "thrForce"
    moduleOutput = unitTestSim.pullMessageLogData(moduleConfig.outputDataName + '.' + moduleOutputName,
                                                  range(MAX_EFF_CNT))


    truthVector = results_thrForceMapping(requestedTorque, moduleConfig.controlAxes_B,
                                         vehicleConfigOut.CoM_B, rcsLocationData,
                                         rcsDirectionData, moduleConfig.thrForceSign,
                                         moduleConfig.thrForcMag, moduleConfig.angErrThresh,
                                         numThrusters)

    trueVector = np.zeros((2, MAX_EFF_CNT))
    trueVector[0,:] = truthVector
    trueVector[1,:] = truthVector

    accuracy = 1e-6


    D = rcsDirectionData
    F = np.transpose(moduleOutput[0, 0:MAX_EFF_CNT])
    receivedTorque = -1.0 * np.array([np.matmul(np.transpose(D), F)])
    receivedTorque = np.append(np.array([0.0]), receivedTorque)

    Lr_offset = np.array([0.0, 0.0, 0.0])
    Lr_Bar = np.array([0.0, 0.0, 0.0])
    for i in range(0,numThrusters):
        if moduleConfig.thrForceSign < 0 and moduleConfig.thrForcMag[i] >= 0:
            Lr_offset -= moduleConfig.thrForcMag[i]*np.cross(rcsLocationData[i,:]-CoM_B,rcsDirectionData[i,:])

    Lr_Bar = requestedTorque + Lr_offset

    '''
    if numThrusters >= moduleConfig.numControlAxes:
        testFailCount, testMessages = unitTestSupport.compareArrayND(np.array([requestedTorque]),
                                                                     np.array([receivedTorque]), accuracy,
                                                                     "CompareTorques",
                                                                     moduleConfig.numControlAxes, testFailCount, testMessages)
    '''

    snippetName = "LrBReq_LrBRec_" + str(useDVThruster) + "_" + str(useCOMOffset) + "_" + str(dropThruster) + "_" + str(dropAxis) + "_" + str(saturateThrusters)
    requestedTex = str(Lr_Bar) #str(requestedTorque)
    receivedTex = str(receivedTorque[1:4])
    snippetTex = "Requested:\t" + requestedTex + "\n"
    snippetTex += "Received:\t" + receivedTex + "\n"

    unitTestSupport.writeTeXSnippet("Torques/"+snippetName, snippetTex, path)

    # compare the module results to the truth values
    for i in range(0,len(trueVector)):
        # check a vector values
        if not unitTestSupport.isArrayEqual(moduleOutput[i], trueVector[i], numThrusters, accuracy):
            testFailCount += 1
            testMessages.append("FAILED: " + moduleWrap.ModelTag + " Module failed " +
                                moduleOutputName + " unit test at t=" +
                                str(moduleOutput[i,0]*macros.NANO2SEC) +
                                "sec\n")

    unitTestSupport.writeTeXSnippet('toleranceValue', str(accuracy), path)

    snippentName = "passFail_" + str(useDVThruster) + "_" + str(useCOMOffset) + "_" + str(dropThruster) + "_" + str(dropAxis) + "_" + str(saturateThrusters)
    if testFailCount == 0:
        colorText = 'ForestGreen'
        print "PASSED: " + moduleWrap.ModelTag
        passedText = '\\textcolor{' + colorText + '}{' + "PASSED" + '}'
    else:
        colorText = 'Red'
        print "Failed: " + moduleWrap.ModelTag
        passedText = '\\textcolor{' + colorText + '}{' + "Failed" + '}'
    unitTestSupport.writeTeXSnippet(snippentName, passedText, path)

    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]


#
# This statement below ensures that the unitTestScript can be run as a
# stand-along python script
#
if __name__ == "__main__":
    test_module(              # update "module" in function name
                 False,
                 False,           # useDVThruster
                 False,           # use COM offset
                 False,           # drop thruster(s)
                 False,           # drop control axis
                 0,               # saturateThrusters
                 False            # misconfigThruster

    )
