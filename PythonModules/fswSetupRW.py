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
#   FSW Setup Utilities for RW
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




rwList = []

#
#   This function is called to setup a FSW RW device in python, and adds it to the of RW
#   devices in rwList[].  This list is accessible from the parent python script that
#   imported this rw library script, and thus any particular value can be over-ridden
#   by the user.
#
def create(
        gsHat_S,
        Js
    ):
    global rwList

    # create the blank RW object
    RW = vehicleConfigData.RWConfigurationElement()


    RW.gsHat_S = gsHat_S
    RW.Js = Js

    # add RW to the list of RW devices
    rwList.append(RW)

    return

#
#   This function should be called after all devices are created with create()
#   It creates the C-class container for the array of RW devices, and attaches
#   this container to the spacecraft object
#
def addToSpacecraft(rwConfigMsgName, simObject, processName):
    global rwList

    rwClass = vehicleConfigData.RWConstellation()

    i = 0
    for item in rwList:
        vehicleConfigData.RWConfigArray_setitem(rwClass.reactionWheels, i, item)
        i += 1

    inputMessageSize = vehicleConfigData.MAX_EFF_CNT*(3+1+3)*8 + 4

    rwClass.numRW = len(rwList)

    simObject.CreateNewMessage(processName,
                               rwConfigMsgName,
                               inputMessageSize,
                               2)
    simObject.WriteMessageData( rwConfigMsgName,
                                inputMessageSize,
                                0,
                                rwClass)

    return

def clearSetup():
    global rwList

    rwList = []

    return

def getNumOfDevices():
    return len(rwList)
