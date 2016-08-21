'''
Copyright (c) 2016, Autonomous Vehicle Systems Lab, Univeristy of Colorado at Boulder

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
#   FSW Setup Utilities for Thrusters
#

import sys, os, inspect
import math
import numpy

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('Basilisk')
sys.path.append(splitPath[0] + '/Basilisk/modules')
sys.path.append(splitPath[0] + '/Basilisk/PythonModules')

import SimulationBaseClass
import vehicleConfigData




thrList = []

#
#   This function is called to setup a FSW RW device in python, and adds it to the of RW
#   devices in rwList[].  This list is accessible from the parent python script that
#   imported this rw library script, and thus any particular value can be over-ridden
#   by the user.
#
def create(
        rThrust_S,
        tHatThrust_S,
        minPulseTime = 0.020
    ):
    global thrList

    # create the blank Thruster object
    thrPointer = vehicleConfigData.ThrusterPointData()

    thrPointer.rThrust_S = rThrust_S
    thrPointer.tHatThrust_S = tHatThrust_S

    # add RW to the list of RW devices
    thrList.append(thrPointer)

    return

#
#   This function should be called after all devices are created with create()
#   It creates the C-class container for the array of RW devices, and attaches
#   this container to the spacecraft object
#
def addToSpacecraft(thrConfigMsgName, simObject, processName):
    global thrList

    thrClass = vehicleConfigData.ThrusterCluster()

    i = 0
    for item in thrList:
        vehicleConfigData.ThrustConfigArray_setitem(thrClass.thrusters, i, item)
        i += 1

    messageSize = vehicleConfigData.MAX_EFF_CNT*(3+3)*8 + 4

    thrClass.numThrusters = len(thrList)

    simObject.CreateNewMessage(processName,
                               thrConfigMsgName,
                               messageSize,
                               2)
    simObject.WriteMessageData(thrConfigMsgName,
                               messageSize,
                               0,
                               thrClass)

    return

def clearSetup():
    global thrList

    thrList = []

    return

def getNumOfDevices():
    return len(thrList)
