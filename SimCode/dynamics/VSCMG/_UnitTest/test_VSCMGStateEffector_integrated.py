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
import sys, os, inspect
import numpy as np
import pytest
import math

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('SimCode')
sys.path.append(splitPath[0] + '/modules')
sys.path.append(splitPath[0] + '/PythonModules')

import SimulationBaseClass
import unitTestSupport  # general support file with common unit test functions
import matplotlib as mpl
import matplotlib.pyplot as plt
import spacecraftPlus
import sim_model
import macros
import gravityEffector
import spice_interface
import VSCMGStateEffector

mpl.rc("figure", figsize=(5.75,4))

rpm2rad = 2.*math.pi/60.

def defaultVSCMG():
    VSCMG = VSCMGStateEffector.VSCMGConfigSimMsg()
    VSCMG.typeName = 'Honeywell_HR16'
    VSCMG.rWB_S = [[0.],[0.],[0.]]
    VSCMG.gsHat_S = [[0.],[0.],[0.]]
    VSCMG.w2Hat0_S = [[0.], [0.], [0.]]
    VSCMG.w3Hat0_S = [[0.], [0.], [0.]]
    VSCMG.rWB_B = [[0.],[0.],[0.]]
    VSCMG.gsHat_B = [[0.],[0.],[0.]]
    VSCMG.w2Hat0_B = [[0.],[0.],[0.]]
    VSCMG.w3Hat0_B = [[0.],[0.],[0.]]
    VSCMG.w2Hat_B = [[0.],[0.],[0.]]
    VSCMG.w3Hat_B = [[0.],[0.],[0.]]
    VSCMG.theta = 0.
    VSCMG.u_current = 0.
    VSCMG.u_max = 0.2
    VSCMG.u_min = 0.
    VSCMG.u_f = 0.
    VSCMG.Omega = 0.
    VSCMG.Omega_max = 6000. * rpm2rad
    VSCMG.Js = 100./VSCMG.Omega_max # 0.159154943092
    VSCMG.Jt = 0.5*VSCMG.Js # 0.0795774715459
    VSCMG.Jg = 0.5*VSCMG.Js # 0.0795774715459
    VSCMG.U_s = 4.8e-06 * 1e4
    VSCMG.U_d = 1.54e-06 * 1e4
    VSCMG.mass = 12.
    VSCMG.linearFrictionRatio = -1
    VSCMG.RWModel = 0
    return VSCMG


@pytest.mark.parametrize("useFlag, testCase", [
    (False,'BalancedWheels'),
    (False,'JitterSimple'),
    (False,'JitterFullyCoupled')
])

# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail() # need to update how the RW states are defined
# provide a unique test method name, starting with test_
def test_VSCMGIntegratedTest(show_plots,useFlag,testCase):
    [testResults, testMessage] = VSCMGIntegratedTest(show_plots,useFlag,testCase)
    assert testResults < 1, testMessage

def VSCMGIntegratedTest(show_plots,useFlag,testCase):
    # The __tracebackhide__ setting influences pytest showing of tracebacks:
    # the mrp_steering_tracking() function will not be shown unless the
    # --fulltrace command line option is specified.
    __tracebackhide__ = True

    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty list to store test log messages

    scObject = spacecraftPlus.SpacecraftPlus()
    scObject.ModelTag = "spacecraftBody"

    unitTaskName = "unitTask"  # arbitrary name (don't change)
    unitProcessName = "TestProcess"  # arbitrary name (don't change)
    rwCommandName = "vscmg_cmds"

    #   Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()
    unitTestSim.TotalSim.terminateSimulation()

    # Create test thread
    testProcessRate = macros.sec2nano(0.001)  # update process rate update time
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, testProcessRate))

    # add RW devices

    VSCMGs = []

    VSCMGs.append(defaultVSCMG())
    VSCMGs[0].gsHat_S = [[1.0], [0.0], [0.0]]
    VSCMGs[0].w2Hat0_S = [[0.0], [0.0], [1.0]]
    VSCMGs[0].w3Hat0_S = [[0.0], [-1.0], [0.0]]
    VSCMGs[0].Omega = 500 * rpm2rad # 52.3598775598
    VSCMGs[0].rWB_S = [[0.1], [0.0], [0.0]]

    VSCMGs.append(defaultVSCMG())
    VSCMGs[1].gsHat_S = [[0.0], [1.0], [0.0]]
    VSCMGs[1].w2Hat0_S = [[0.0], [0.0], [-1.0]]
    VSCMGs[1].w3Hat0_S = [[-1.0], [0.0], [0.0]]
    VSCMGs[1].Omega =  200 * rpm2rad # 20.9439510239
    VSCMGs[1].rWB_S = [[0.0], [0.1], [0.0]]

    VSCMGs.append(defaultVSCMG())
    VSCMGs[2].gsHat_S = [[0.0], [0.0], [1.0]]
    VSCMGs[2].w2Hat0_S = [[0.0], [1.0], [0.0]]
    VSCMGs[2].w3Hat0_S = [[-1.0], [0.0], [0.0]]
    VSCMGs[2].Omega = -150 * rpm2rad # -15.7079632679
    VSCMGs[2].rWB_S = [[0.0], [0.0], [0.1]]

    if testCase == 'BalancedWheels':
        VSCMGModel = 0
    elif testCase == 'JitterSimple':
        VSCMGModel = 1
    elif testCase == 'JitterFullyCoupled':
        VSCMGModel = 2

    for VSCMG in VSCMGs:
        VSCMG.RWModel = VSCMGModel

    # create RW object container and tie to spacecraft object
    rwStateEffector = VSCMGStateEffector.VSCMGStateEffector()
    rwStateEffector.ModelTag = "VSCMGs"
    for item in VSCMGs:
        rwStateEffector.AddReactionWheel(item)
    scObject.addStateEffector(rwStateEffector)

    # set RW torque command
    cmdArray = VSCMGStateEffector.VSCMGArrayTorqueIntMsg()
    cmdArray.wheelTorque = [0.20, 0.10, -0.50] # [Nm]
    unitTestSupport.setMessage(unitTestSim.TotalSim,
                               unitProcessName,
                               rwCommandName,
                               cmdArray)

    # Add test module to runtime call list
    unitTestSim.AddModelToTask(unitTaskName, rwStateEffector)
    unitTestSim.AddModelToTask(unitTaskName, scObject)

    unitTestSim.earthGravBody = gravityEffector.GravBodyData()
    unitTestSim.earthGravBody.bodyInMsgName = "earth_planet_data"
    unitTestSim.earthGravBody.outputMsgName = "earth_display_frame_data"
    unitTestSim.earthGravBody.mu = 0.3986004415E+15 # meters!
    unitTestSim.earthGravBody.isCentralBody = True
    unitTestSim.earthGravBody.useSphericalHarmParams = False

    earthEphemData = spice_interface.SpicePlanetStateSimMsg()
    earthEphemData.J2000Current = 0.0
    earthEphemData.PositionVector = [0.0, 0.0, 0.0]
    earthEphemData.VelocityVector = [0.0, 0.0, 0.0]
    earthEphemData.J20002Pfix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    earthEphemData.J20002Pfix_dot = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    earthEphemData.PlanetName = "earth"

    scObject.gravField.gravBodies = spacecraftPlus.GravBodyVector([unitTestSim.earthGravBody])

    # log data
    unitTestSim.TotalSim.logThisMessage(scObject.scStateOutMsgName, testProcessRate)
    unitTestSim.TotalSim.logThisMessage(rwStateEffector.OutputDataString, testProcessRate)

    msgSize = earthEphemData.getStructSize()
    unitTestSim.TotalSim.CreateNewMessage(unitProcessName,
        unitTestSim.earthGravBody.bodyInMsgName, msgSize, 2)
    unitTestSim.TotalSim.WriteMessageData(unitTestSim.earthGravBody.bodyInMsgName, msgSize, 0, earthEphemData)

    unitTestSim.InitializeSimulation()

    unitTestSim.AddVariableForLogging(scObject.ModelTag + ".totOrbAngMomPntN_N", testProcessRate, 0, 2, 'double')
    unitTestSim.AddVariableForLogging(scObject.ModelTag + ".totRotAngMomPntC_N", testProcessRate, 0, 2, 'double')

    posRef = scObject.dynManager.getStateObject("hubPosition")
    velRef = scObject.dynManager.getStateObject("hubVelocity")
    sigmaRef = scObject.dynManager.getStateObject("hubSigma")
    omegaRef = scObject.dynManager.getStateObject("hubOmega")

    posRef.setState([[-4020338.690396649],	[7490566.741852513],	[5248299.211589362]])
    velRef.setState([[-5199.77710904224],	[-3436.681645356935],	[1041.576797498721]])
    sigmaRef.setState([[0.0], [0.0], [0.0]])
    omegaRef.setState([[0.08], [0.01], [0.0]])

    scObject.hub.mHub = 750.0
    scObject.hub.r_BcB_B = [[-0.0002], [0.0001], [0.1]]
    scObject.hub.IHubPntBc_B = [[900.0, 0.0, 0.0], [0.0, 800.0, 0.0], [0.0, 0.0, 600.0]]

    stopTime = 5.
    unitTestSim.ConfigureStopTime(macros.sec2nano(stopTime))
    unitTestSim.ExecuteSimulation()

    orbAngMom_N = unitTestSim.GetLogVariableData(scObject.ModelTag + ".totOrbAngMomPntN_N")
    rotAngMom_N = unitTestSim.GetLogVariableData(scObject.ModelTag + ".totRotAngMomPntC_N")

    wheelSpeeds = unitTestSim.pullMessageLogData(rwStateEffector.OutputDataString + "." + "wheelSpeeds",range(3))
    sigmaData = unitTestSim.pullMessageLogData(scObject.scStateOutMsgName+'.sigma_BN',range(3))
    omegaData = unitTestSim.pullMessageLogData(scObject.scStateOutMsgName+'.omega_BN_B',range(3))

    # rotEnergy = unitTestSim.GetLogVariableData(scObject.ModelTag + ".totRotEnergy")
    # orbKinEnergy = unitTestSim.GetLogVariableData(scObject.ModelTag + ".totOrbKinEnergy")

    dataPos = posRef.getState()
    dataSigma = sigmaRef.getState()
    dataPos = [[stopTime, dataPos[0][0], dataPos[1][0], dataPos[2][0]]]
    dataSigma = [[stopTime, dataSigma[0][0], dataSigma[1][0], dataSigma[2][0]]]


    if testCase == 'BalancedWheels':
        truePos = [
            [-4046317.446006109, 7473345.937334083, 5253480.873774451]
        ]

        trueSigma = [
            [0.09973672149864025, 0.011213339971279653, 0.0003115172941344355]
        ]

    elif testCase == 'JitterSimple':
        truePos = [
            [-4046317.4472558703, 7473345.920433197, 5253480.873665418]
        ]

        trueSigma = [
            [0.09925443342446622, 0.010153635701299952, -6.716226879431521e-05]
        ]

    elif testCase == 'JitterFullyCoupled':
        truePos = [
            [-4046317.4472384057, 7473345.921374322, 5253480.873495584]
        ]

        trueSigma = [
            [0.09926551360276777, 0.010153926978972804, -6.141297232067025e-05]
        ]



    initialOrbAngMom_N = [
                [orbAngMom_N[0,1], orbAngMom_N[0,2], orbAngMom_N[0,3]]
                ]

    finalOrbAngMom = [
                [orbAngMom_N[-1,0], orbAngMom_N[-1,1], orbAngMom_N[-1,2], orbAngMom_N[-1,3]]
                 ]

    initialRotAngMom_N = [
                [rotAngMom_N[0,1], rotAngMom_N[0,2], rotAngMom_N[0,3]]
                ]

    finalRotAngMom = [
                [rotAngMom_N[-1,0], rotAngMom_N[-1,1], rotAngMom_N[-1,2], rotAngMom_N[-1,3]]
                 ]


    # plt.figure(1)
    # plt.plot(orbAngMom_N[:,0]*1e-9, orbAngMom_N[:,1] - orbAngMom_N[0,1], orbAngMom_N[:,0]*1e-9, orbAngMom_N[:,2] - orbAngMom_N[0,2], orbAngMom_N[:,0]*1e-9, orbAngMom_N[:,3] - orbAngMom_N[0,3])
    # plt.title("Change in Orbital Angular Momentum")
    #
    # plt.figure(2)
    # plt.plot(rotAngMom_N[:,0]*1e-9, rotAngMom_N[:,1] - rotAngMom_N[0,1], rotAngMom_N[:,0]*1e-9, rotAngMom_N[:,2] - rotAngMom_N[0,2], rotAngMom_N[:,0]*1e-9, rotAngMom_N[:,3] - rotAngMom_N[0,3])
    # plt.title("Change in Rotational Angular Momentum")
    #
    # plt.figure(3)
    # for i in range(1,4):
    #     plt.subplot(4,1,i)
    #     plt.plot(wheelSpeeds[:,0]*1.0E-9, wheelSpeeds[:,i] / (2.0 * math.pi) * 60, label='RWA' + str(i))
    #     plt.xlabel('Time (s)')
    #     plt.ylabel(r'RW' + str(i) + r' $\Omega$ (RPM)')
    #
    # plt.figure(4)
    # for i in range(1,4):
    #     plt.subplot(4,1,i)
    #     plt.plot(sigmaData[:,0]*1.0E-9, sigmaData[:,i], label='MRP' + str(i))
    #     plt.xlabel('Time (s)')
    #     plt.ylabel(r'MRP b' + str(i))

    thetaData = np.empty([len(sigmaData[:,0]),2])
    thetaData[:,0] = sigmaData[:,0]
    for i in range(0,len(sigmaData[:,0])):
        thetaData[i,1] = 4*np.arctan(np.linalg.norm(sigmaData[i,1:]))
    thetaFit = np.empty([len(sigmaData[:,0]),2])
    thetaFit[:,0] = thetaData[:,0]
    fitOrd = 2
    p = np.polyfit(thetaData[:,0]*1e-9,thetaData[:,1],fitOrd)
    thetaFit[:,1] = np.polyval(p,thetaFit[:,0]*1e-9)

    # plt.figure(5)
    # plt.plot(thetaData[:,0]*1e-9, thetaData[:,1])
    # plt.plot(thetaFit[:,0]*1e-9, thetaFit[:,1], 'r--')
    # plt.title("Principle Angle")
    # plt.xlabel('Time (s)')
    # plt.ylabel(r'$\theta$ (deg)')

    plt.figure(6)
    plt.plot(thetaData[:,0]*1e-9, thetaData[:,1]-thetaFit[:,1])
    plt.title("Principle Angle Fit")
    plt.xlabel('Time (s)')
    plt.ylabel(r'$\theta$ (deg)')

    # plt.figure(7)
    # for i in range(1,4):
    #     plt.subplot(4,1,i)
    #     plt.plot(omegaData[:,0]*1.0E-9, omegaData[:,i] * 180/math.pi, label='omega' + str(i))
    #     plt.xlabel('Time (s)')
    #     plt.ylabel(r'b' + str(i) + r' $\omega$ (d/s)')

    if show_plots == True:
        plt.show()


    accuracy = 1e-8
    for i in range(0,len(truePos)):
        # check a vector values
        if not unitTestSupport.isArrayEqualRelative(dataPos[i],truePos[i],3,accuracy):
            testFailCount += 1
            testMessages.append("FAILED: Reaction Wheel Integrated Test failed pos unit test")

    for i in range(0,len(trueSigma)):
        # check a vector values
        if not unitTestSupport.isArrayEqualRelative(dataSigma[i],trueSigma[i],3,accuracy):
            testFailCount += 1
            testMessages.append("FAILED: Reaction Wheel Integrated Test failed attitude unit test")

    if testCase == 'BalancedWheels' or testCase == 'JitterFullyCoupled':
        for i in range(0,len(initialOrbAngMom_N)):
            # check a vector values
            if not unitTestSupport.isArrayEqualRelative(finalOrbAngMom[i],initialOrbAngMom_N[i],3,accuracy):
                testFailCount += 1
                testMessages.append("FAILED: Reaction Wheel Integrated Test failed orbital angular momentum unit test")

        for i in range(0,len(initialRotAngMom_N)):
            # check a vector values
            if not unitTestSupport.isArrayEqualRelative(finalRotAngMom[i],initialRotAngMom_N[i],3,accuracy):
                testFailCount += 1
                testMessages.append("FAILED: Reaction Wheel Integrated Test failed rotational angular momentum unit test")

    if testFailCount == 0:
        print "PASSED: " + " Reaction Wheel Integrated Sim Test"

    assert testFailCount < 1, testMessages

    # return fail count and join into a single string all messages in the list
    # testMessage
    return [testFailCount, ''.join(testMessages)]

if __name__ == "__main__":
    VSCMGIntegratedTest(True,False,'BalancedWheels')