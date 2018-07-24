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
#   Module Name:        cssWlsEst()
#   Author:             Hanspeter Schaub
#   Creation Date:      April 29, 2018
#

import pytest
import sys, os, inspect
# import packages as needed e.g. 'numpy', 'ctypes, 'math' etc.
import numpy
import math
import logging

# Import all of the modules that we are going to be called in this simulation
from Basilisk.utilities import SimulationBaseClass
from Basilisk.utilities import unitTestSupport                  # general support file with common unit test functions
import matplotlib.pyplot as plt
from Basilisk.utilities import macros
from Basilisk.fswAlgorithms import cssWlsEst
from Basilisk.fswAlgorithms import fswMessages
from Basilisk.simulation import simFswInterfaceMessages

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))





# Function that takes a sun pointing vector and array of CSS normal vectors and
# returns the measurements associated with those normal vectors.
def createCosList(sunPointVec, sensorPointList):
    outList = []
    for sensorPoint in sensorPointList:
        outList.append(numpy.dot(sunPointVec, sensorPoint))
    return outList


# Method that checks that all of the numActive outputs from the data array
# that are greater than threshold thresh are consistent with the values in
# measVec
def checkNumActiveAccuracy(measVec, numActiveUse, numActiveFailCriteria, thresh):
    numActivePred = 0
    testFailCount = 0
    # Iterate through measVec and find all valid signals
    for i in range(0, 32):
        obsVal = measVec.CosValue[i]
        if (obsVal > thresh):
            numActivePred += 1

    # Iterate through the numActive array and sum up all numActive estimates
    numActiveTotal = numpy.array([0.])
    j = 0
    while j < numActiveUse.shape[0]:
        numActiveTotal += numActiveUse[j, 1:]
        j += 1
    numActiveTotal /= j  # Mean number of numActive
    # If we violate the test criteria, increment the failure count and alert user
    if (abs(numActiveTotal[0] - numActivePred) > numActiveFailCriteria):
        testFailCount += 1
        errorString = "Active number failure for count of: "
        errorString += str(numActivePred)
        logging.error(errorString)
    return testFailCount


# This method takes the sHat estimate output by the estimator and compares that
# against the actual sun vector passed in as an argument.  If it doesn't match
# to the specified tolerance, increment failure counter and alert the user
def checksHatAccuracy(testVec, sHatEstUse, angleFailCriteria, TotalSim):
    j = 0
    testFailCount = 0
    sHatTotal = numpy.array([0.0, 0.0, 0.0])
    # Sum up all of the sHat estimates from the execution
    while j < sHatEstUse.shape[0]:
        sHatTotal += sHatEstUse[j, 1:]
        j += 1
    sHatTotal /= j  # mean sHat estimate
    # This logic is to protect cases where the dot product numerically breaks acos
    dot_value = numpy.dot(sHatTotal, testVec)
    if (abs(dot_value > 1.0)):
        dot_value -= 2.0 * (dot_value - math.copysign(1.0, dot_value))

    # If we violate the failure criteria, increment failure count and alert user
    if (abs(math.acos(dot_value)) > angleFailCriteria):
        testFailCount += 1
        errorString = "Angle fail criteria violated for test vector:"
        errorString += str(testVec).strip('[]') + "\n"
        errorString += "Criteria violation of: "
        errorString += str(abs(math.acos(numpy.dot(sHatTotal, testVec))))
        logging.error(errorString)
    return testFailCount




# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail(conditionstring)

@pytest.mark.parametrize("testSunHeading, testRate", [
     ("True", "False")
    ,("False", "True")
])


# provide a unique test method name, starting with test_
def test_module(show_plots, testSunHeading, testRate):     # update "module" in this function name to reflect the module name
    # each test method requires a single assert method to be called
    # pass on the testPlotFixture so that the main test function may set the DataStore attributes

    if testSunHeading:
        [testResults, testMessage] = cssWlsEstTestFunction(show_plots)
        assert testResults < 1, testMessage

    if testRate:
        [testResults, testMessage] = cssRateTestFunction(show_plots)
        assert testResults < 1, testMessage


def cssWlsEstTestFunction(show_plots):
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages
    unitTaskName = "unitTask"               # arbitrary name (don't change)
    unitProcessName = "TestProcess"         # arbitrary name (don't change)

    # Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()
    unitTestSim.TotalSim.terminateSimulation()

    # Create test thread
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, int(1E8)))

    # Construct algorithm and associated C++ container
    CSSWlsEstFSWConfig = cssWlsEst.CSSWLSConfig()
    CSSWlsWrap = unitTestSim.setModelDataWrap(CSSWlsEstFSWConfig)
    CSSWlsWrap.ModelTag = "CSSWlsEst"

    # Add module to runtime call list
    unitTestSim.AddModelToTask(unitTaskName, CSSWlsWrap, CSSWlsEstFSWConfig)

    # Initialize the WLS estimator configuration data
    CSSWlsEstFSWConfig.cssDataInMsgName = "css_data_aggregate"
    CSSWlsEstFSWConfig.cssConfigInMsgName = "css_config_data"
    CSSWlsEstFSWConfig.navStateOutMsgName = "css_nav_sunHeading"
    CSSWlsEstFSWConfig.useWeights = False
    CSSWlsEstFSWConfig.sensorUseThresh = 0.15

    CSSOrientationList = [
        [0.70710678118654746, -0.5, 0.5],
        [0.70710678118654746, -0.5, -0.5],
        [0.70710678118654746, 0.5, -0.5],
        [0.70710678118654746, 0.5, 0.5],
        [-0.70710678118654746, 0, 0.70710678118654757],
        [-0.70710678118654746, 0.70710678118654757, 0.0],
        [-0.70710678118654746, 0, -0.70710678118654757],
        [-0.70710678118654746, -0.70710678118654757, 0.0],
    ]
    numCSS = len(CSSOrientationList)

    # set the CSS unit vectors
    cssConfigData = fswMessages.CSSConfigFswMsg()
    totalCSSList = []
    for CSSHat in CSSOrientationList:
        CSSConfigElement = fswMessages.CSSUnitConfigFswMsg()
        CSSConfigElement.CBias = 1.0
        CSSConfigElement.nHat_B = CSSHat
        totalCSSList.append(CSSConfigElement)
    cssConfigData.nCSS = numCSS
    cssConfigData.cssVals = totalCSSList
    unitTestSupport.setMessage(unitTestSim.TotalSim,
                               unitProcessName,
                               CSSWlsEstFSWConfig.cssConfigInMsgName,
                               cssConfigData)

    # Initialize input message
    cssDataMsg = simFswInterfaceMessages.CSSArraySensorIntMsg()
    unitTestSupport.setMessage(unitTestSim.TotalSim,
                               unitProcessName,
                               CSSWlsEstFSWConfig.cssDataInMsgName,
                               cssDataMsg)

    angleFailCriteria = 17.5 * math.pi / 180.0  # Get 95% effective charging in this case
    numActiveFailCriteria = 0.000001  # basically zero

    # Log the output message as well as the internal numACtiveCss variables
    unitTestSim.TotalSim.logThisMessage(CSSWlsEstFSWConfig.navStateOutMsgName, int(1E8))
    unitTestSim.AddVariableForLogging("CSSWlsEst.numActiveCss", int(1E8))

    # Initial test is all of the principal body axes
    TestVectors = [[-1.0, 0.0, 0.0],
                   [0.0, -1.0, 0.0],
                   [1.0, 0.0, 0.0],
                   [0.0, 1.0, 0.0],
                   [0.0, 0.0, -1.0],
                   [0.0, 0.0, 1.0]]

    # Initialize test and then step through all of the test vectors in a loop
    unitTestSim.InitializeSimulation()
    CSSWlsWrap.Reset(0)     # this module reset function needs a time input (in NanoSeconds)

    stepCount = 0
    logLengthPrev = 0

    truthData = []
    for testVec in TestVectors:
        if (stepCount > 1):  # Doing this to test permutations and get code coverage
            CSSWlsEstFSWConfig.useWeights = True

        # Get observation data based on sun pointing and CSS orientation data
        cssDataMsg.CosValue = createCosList(testVec, CSSOrientationList)

        # Write in the observation data to the input message
        unitTestSim.TotalSim.WriteMessageData(CSSWlsEstFSWConfig.cssDataInMsgName,
                                              cssDataMsg.getStructSize(),
                                              0,
                                              cssDataMsg)

        # Increment the stop time to new termination value
        unitTestSim.ConfigureStopTime(int((stepCount + 1) * 1E9))
        # Execute simulation to current stop time
        unitTestSim.ExecuteSimulation()
        stepCount += 1

        # Pull logged data out into workspace for analysis
        sHatEst = unitTestSim.pullMessageLogData(CSSWlsEstFSWConfig.navStateOutMsgName + '.vehSunPntBdy',
                                                 range(3))

        numActive = unitTestSim.GetLogVariableData("CSSWlsEst.numActiveCss")
        sHatEstUse = sHatEst[logLengthPrev:, :]  # Only data for this subtest
        numActiveUse = numActive[logLengthPrev + 1:, :]  # Only data for this subtest

        # Check failure criteria and add test failures
        testFailCount += checksHatAccuracy(testVec, sHatEstUse, angleFailCriteria,
                                           unitTestSim)
        testFailCount += checkNumActiveAccuracy(cssDataMsg, numActiveUse,
                                                numActiveFailCriteria, CSSWlsEstFSWConfig.sensorUseThresh)

        # Pop truth state onto end of array for plotting purposes
        currentRow = [sHatEstUse[0, 0]]
        currentRow.extend(testVec)
        truthData.append(currentRow)
        currentRow = [sHatEstUse[-1, 0]]
        currentRow.extend(testVec)
        truthData.append(currentRow)
        logLengthPrev = sHatEst.shape[0]

    # Hand construct case where we get low coverage (2 valid sensors)
    LonVal = 0.0
    LatVal = 40.68 * math.pi / 180.0
    doubleTestVec = [math.sin(LatVal), math.cos(LatVal) * math.sin(LonVal),
                     math.cos(LatVal) * math.cos(LonVal)]
    cssDataMsg.CosValue = createCosList(doubleTestVec, CSSOrientationList)

    # Write in double coverage conditions and ensure that we get correct outputs
    unitTestSim.TotalSim.WriteMessageData(CSSWlsEstFSWConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(int((stepCount + 1) * 1E9))
    unitTestSim.ExecuteSimulation()
    stepCount += 1
    sHatEst = unitTestSim.pullMessageLogData(CSSWlsEstFSWConfig.navStateOutMsgName + '.vehSunPntBdy',
                                             range(3))
    numActive = unitTestSim.GetLogVariableData("CSSWlsEst.numActiveCss")
    sHatEstUse = sHatEst[logLengthPrev:, :]
    numActiveUse = numActive[logLengthPrev + 1:, :]
    logLengthPrev = sHatEst.shape[0]
    currentRow = [sHatEstUse[0, 0]]
    currentRow.extend(doubleTestVec)
    truthData.append(currentRow)
    currentRow = [sHatEstUse[-1, 0]]
    currentRow.extend(doubleTestVec)
    truthData.append(currentRow)

    # Check test criteria again
    testFailCount += checksHatAccuracy(doubleTestVec, sHatEstUse, angleFailCriteria,
                                       unitTestSim)
    testFailCount += checkNumActiveAccuracy(cssDataMsg, numActiveUse,
                                            numActiveFailCriteria, CSSWlsEstFSWConfig.sensorUseThresh)

    # Same test as above, but zero first element to get to a single coverage case
    cssDataMsg.CosValue[0] = 0.0
    unitTestSim.TotalSim.WriteMessageData(CSSWlsEstFSWConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(int((stepCount + 1) * 1E9))
    unitTestSim.ExecuteSimulation()
    stepCount += 1
    numActive = unitTestSim.GetLogVariableData("CSSWlsEst.numActiveCss")
    numActiveUse = numActive[logLengthPrev + 1:, :]
    sHatEst = unitTestSim.pullMessageLogData(CSSWlsEstFSWConfig.navStateOutMsgName + '.vehSunPntBdy',
                                             range(3))
    sHatEstUse = sHatEst[logLengthPrev + 1:, :]
    logLengthPrev = sHatEst.shape[0]
    testFailCount += checkNumActiveAccuracy(cssDataMsg, numActiveUse,
                                            numActiveFailCriteria, CSSWlsEstFSWConfig.sensorUseThresh)
    currentRow = [sHatEstUse[0, 0]]
    currentRow.extend(doubleTestVec)
    truthData.append(currentRow)
    currentRow = [sHatEstUse[-1, 0]]
    currentRow.extend(doubleTestVec)
    truthData.append(currentRow)

    # Same test as above, but zero first and fourth elements to get to zero coverage
    cssDataMsg.CosValue[0] = 0.0
    cssDataMsg.CosValue[3] = 0.0
    unitTestSim.TotalSim.WriteMessageData(CSSWlsEstFSWConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(int((stepCount + 1) * 1E9))
    unitTestSim.ExecuteSimulation()
    numActive = unitTestSim.GetLogVariableData("CSSWlsEst.numActiveCss")
    numActiveUse = numActive[logLengthPrev:, :]
    logLengthPrev = numActive.shape[0]
    testFailCount += checkNumActiveAccuracy(cssDataMsg, numActiveUse,
                                            numActiveFailCriteria, CSSWlsEstFSWConfig.sensorUseThresh)

    # Format data for plotting
    truthData = numpy.array(truthData)
    sHatEst = unitTestSim.pullMessageLogData(CSSWlsEstFSWConfig.navStateOutMsgName + '.vehSunPntBdy',
                                             range(3))
    numActive = unitTestSim.GetLogVariableData("CSSWlsEst.numActiveCss")


    #
    # test the case where all CSS signals are zero
    #
    cssDataMsg.CosValue = numpy.zeros(len(CSSOrientationList))
    unitTestSim.TotalSim.WriteMessageData(CSSWlsEstFSWConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(int((stepCount + 2) * 1E9))
    unitTestSim.ExecuteSimulation()
    sHatEstZero = unitTestSim.pullMessageLogData(CSSWlsEstFSWConfig.navStateOutMsgName + '.vehSunPntBdy',
                                             range(3))
    sHatEstZeroUse = sHatEstZero[logLengthPrev + 1:, :]

    trueVector = [[0.0, 0.0, 0.0]]*len(sHatEstZeroUse)
    for i in range(0,len(trueVector)):
        # check a vector values
        if not unitTestSupport.isArrayEqual(sHatEstZeroUse[i],trueVector[i],3,1e-12):
            testFailCount += 1
            testMessages.append("FAILED: " + CSSWlsWrap.ModelTag + " Module failed " +
                                CSSWlsEstFSWConfig.navStateOutMsgName + " unit test at t=" +
                                str(sHatEstZeroUse[i,0] * macros.NANO2SEC) +
                                "sec\n")



    if show_plots:
        plt.figure(1)
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 1], label='x-Sun')
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 2], label='y-Sun')
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 3], label='z-Sun')
        plt.legend(loc='upper left')
        plt.xlabel('Time (s)')
        plt.ylabel('Unit Component (--)')

        plt.figure(2)
        plt.plot(numActive[:, 0] * 1.0E-9, numActive[:, 1])
        plt.xlabel('Time (s)')
        plt.ylabel('Number Active CSS (--)')

        plt.figure(3)
        plt.subplot(3, 1, 1)
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 1], label='Est')
        plt.plot(truthData[:, 0] * 1.0E-9, truthData[:, 1], 'r--', label='Truth')
        plt.xlabel('Time (s)')
        plt.ylabel('X Component (--)')
        plt.legend(loc='best')
        plt.subplot(3, 1, 2)
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 2], label='Est')
        plt.plot(truthData[:, 0] * 1.0E-9, truthData[:, 2], 'r--', label='Truth')
        plt.xlabel('Time (s)')
        plt.ylabel('Y Component (--)')
        plt.subplot(3, 1, 3)
        plt.plot(sHatEst[:, 0] * 1.0E-9, sHatEst[:, 3], label='Est')
        plt.plot(truthData[:, 0] * 1.0E-9, truthData[:, 3], 'r--', label='Truth')
        plt.xlabel('Time (s)')
        plt.ylabel('Z Component (--)')
        plt.show()

    #   print out success message if no error were found
    if testFailCount == 0:
        print   "PASSED: " + CSSWlsWrap.ModelTag

    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]


def cssRateTestFunction(show_plots):
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages
    unitTaskName = "unitTask"               # arbitrary name (don't change)
    unitProcessName = "TestProcess"         # arbitrary name (don't change)

    # Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()
    unitTestSim.TotalSim.terminateSimulation()

    # Create test thread
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProcessRate = macros.sec2nano(0.5)  # update process rate update time
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, testProcessRate))

    # Construct algorithm and associated C++ container
    moduleConfig = cssWlsEst.CSSWLSConfig()
    moduleWrap = unitTestSim.setModelDataWrap(moduleConfig)
    moduleWrap.ModelTag = "CSSWlsEst"

    # Add module to runtime call list
    unitTestSim.AddModelToTask(unitTaskName, moduleWrap, moduleConfig)

    # Initialize the WLS estimator configuration data
    moduleConfig.cssDataInMsgName = "css_data_aggregate"
    moduleConfig.cssConfigInMsgName = "css_config_data"
    moduleConfig.navStateOutMsgName = "css_nav_sunHeading"
    moduleConfig.useWeights = False
    moduleConfig.sensorUseThresh = 0.15

    CSSOrientationList = [
        [0.70710678118654746, -0.5, 0.5],
        [0.70710678118654746, -0.5, -0.5],
        [0.70710678118654746, 0.5, -0.5],
        [0.70710678118654746, 0.5, 0.5],
        [-0.70710678118654746, 0, 0.70710678118654757],
        [-0.70710678118654746, 0.70710678118654757, 0.0],
        [-0.70710678118654746, 0, -0.70710678118654757],
        [-0.70710678118654746, -0.70710678118654757, 0.0],
    ]
    numCSS = len(CSSOrientationList)

    # set the CSS unit vectors
    cssConfigData = fswMessages.CSSConfigFswMsg()
    totalCSSList = []
    for CSSHat in CSSOrientationList:
        CSSConfigElement = fswMessages.CSSUnitConfigFswMsg()
        CSSConfigElement.CBias = 1.0
        CSSConfigElement.nHat_B = CSSHat
        totalCSSList.append(CSSConfigElement)
    cssConfigData.nCSS = numCSS
    cssConfigData.cssVals = totalCSSList
    unitTestSupport.setMessage(unitTestSim.TotalSim,
                               unitProcessName,
                               moduleConfig.cssConfigInMsgName,
                               cssConfigData)

    # Initialize input message
    cssDataMsg = simFswInterfaceMessages.CSSArraySensorIntMsg()
    unitTestSupport.setMessage(unitTestSim.TotalSim,
                               unitProcessName,
                               moduleConfig.cssDataInMsgName,
                               cssDataMsg)

    # Log the output message as well as the internal numACtiveCss variables
    unitTestSim.TotalSim.logThisMessage(moduleConfig.navStateOutMsgName, testProcessRate)

    # Get observation data based on sun pointing and CSS orientation data
    cssDataMsg.CosValue = createCosList([1.0, 0.0, 0.0], CSSOrientationList)

    # Write in the observation data to the input message
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)

    # Initialize test and then step through all of the test vectors in a loop
    unitTestSim.InitializeSimulation()
    # Increment the stop time to new termination value
    unitTestSim.ConfigureStopTime(macros.sec2nano(1.0))
    # Execute simulation to current stop time
    unitTestSim.ExecuteSimulation()

    # rotate sun heading by 90 degrees
    cssDataMsg.CosValue = createCosList([0.0, 1.0, 0.0], CSSOrientationList)
    # Write in the observation data to the input message
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(macros.sec2nano(2.0))
    unitTestSim.ExecuteSimulation()

    # test the module reset function
    moduleWrap.Reset(1)     # this module reset function needs a time input (in NanoSeconds)
    unitTestSim.ConfigureStopTime(macros.sec2nano(2.5))
    unitTestSim.ExecuteSimulation()
    cssDataMsg.CosValue = createCosList([1.0, 0.0, 0.0], CSSOrientationList)
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.cssDataInMsgName,
                                          cssDataMsg.getStructSize(),
                                          0,
                                          cssDataMsg)
    unitTestSim.ConfigureStopTime(macros.sec2nano(3.0))
    unitTestSim.ExecuteSimulation()

     # Pull logged data out into workspace for analysis
    omegaEst = unitTestSim.pullMessageLogData(moduleConfig.navStateOutMsgName + '.omega_BN_B',
                                             range(3))
    accuracy = 1e-6
    trueVector = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, -3.14159265],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, +3.14159265]
    ]
    testFailCount, testMessages = unitTestSupport.compareArray(trueVector, omegaEst,
                                                               accuracy, "CSS Rate Vector",
                                                               testFailCount, testMessages)


    #   print out success message if no error were found
    snippentName = "passFailRate"
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
    test_module(
                False,          # show_plots
                False,          # testSunHeading Flag
                True            # testRate Flag
    )
