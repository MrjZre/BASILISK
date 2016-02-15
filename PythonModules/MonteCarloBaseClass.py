import sys, os, inspect #Don't worry about this, standard stuff plus file discovery
import SimulationBaseClass
import random
import abc
import math
import SimulationBaseClass

random.seed(0x1badcad1)


class SingleVariableDispersion(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, varName):
        self.varName = varName

    @abc.abstractmethod
    def generate(self): pass

    @staticmethod
    def checkBounds(value, bounds):
        if value <= bounds[0]:
            return bounds[0]
        if value >= bounds[1]:
            return bounds[1]


class UniformDispersion(SingleVariableDispersion):
    def __init__(self, varName, bounds=None):
        SingleVariableDispersion.__init__(self, varName)
        self.varName = varName
        if bounds is None:
            self.bounds = ([-1.0, 1.0])  # defines a hard floor/ceiling

    def generate(self):
        dispValue = random.uniform(self.bounds[0],self.bounds[1])
        return dispValue


class NormalDispersion(SingleVariableDispersion):
    def __init__(self, varName, bounds=None, mean=0.0, stdDeviation=0.5):
        SingleVariableDispersion.__init__(self, varName)
        self.varName = varName
        if bounds is None:
            self.bounds = ([-1.0, 1.0])  # defines a hard floor/ceiling
        self.mean = mean
        self.stdDeviation = stdDeviation

    def generate(self):
        dispValue = random.gauss(self.mean, self.stdDeviation)
        dispValue = self.checkBounds(dispValue, self.bounds)
        return dispValue


class VectorVariableDispersion(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, varName):
        self.varName = varName
        return

    @abc.abstractmethod
    def generate(self): pass

    @staticmethod
    def checkBounds(value, bounds):
        if value < bounds[0]:
            value = bounds[0]
        if value > bounds[1]:
            value = bounds[1]
        return value

class UniformVectorAngleDispersion(VectorVariableDispersion):
    def __init__(self, varName, phiBounds=None, thetaBounds=None):
        super(UniformVectorAngleDispersion, self).__init__(varName)
        if phiBounds is None:
            self.phiBounds = ([0.0, 2*math.pi])
        else:
            self.phiBounds = phiBounds
        if thetaBounds is None:
            self.thetaBounds = self.phiBounds
        else:
            self.thetaBounds = thetaBounds

    def generate(self):
        phiRnd = random.uniform(self.phiBounds[0], self.phiBounds[1])
        thetaRnd = random.uniform(self.thetaBounds[0], self.thetaBounds[1])
        dispVec = ([math.sin(phiRnd)*math.cos(thetaRnd),
                   math.sin(phiRnd)*math.sin(thetaRnd),
                   phiRnd])
        return dispVec


class NormalVectorAngleDispersion(VectorVariableDispersion):

    def __init__(self, varName, phiStd=0.0, thetaStd=0.0, phiBounds=None, thetaBounds=None):
        super(NormalVectorAngleDispersion, self).__init__(varName)
        self.phiMean = 0.0
        self.phiStd = phiStd  # (rad) angular standard deviation
        self.thetaMean = 0.0
        self.thetaStd = thetaStd  # (rad) angular standard deviation

        if phiBounds is None:
            self.phiBounds = ([0.0, 2*math.pi])
        else:
            self.phiBounds = phiBounds
        if thetaBounds is None:
            self.thetaBounds = self.phiBounds
        else:
            self.thetaBounds = thetaBounds

    def generate(self):
        phiRnd = random.gauss(self.phiMean, self.phiStd)
        phiRnd = self.checkBounds(phiRnd, self.phiBounds)
        thetaRnd = random.gauss(self.thetaMean, self.thetaStd)
        thetaRnd = self.checkBounds(thetaRnd, self.thetaBounds)
        dispVec = ([math.sin(phiRnd)*math.cos(thetaRnd),
                    math.sin(phiRnd)*math.sin(thetaRnd),
                    phiRnd])
        return dispVec


class NormalVectorCartDispersion(VectorVariableDispersion):

    def __init__(self, varName, mean=0.0, stdDeviation=0.0, bounds=None):
        super(NormalVectorCartDispersion, self).__init__(varName)
        self.mean = mean
        self.stdDeviation = stdDeviation
        self.bounds = bounds
        if self.bounds is None:
            self.bounds = ([-1.0, 1.0])

    def generate(self):
        dispVec = []
        for i in range(3):
            rnd = random.gauss(self.mean, self.stdDeviation)
            rnd = self.checkBounds(rnd, self.bounds)
            dispVec.append(rnd)
        return dispVec


class MonteCarloBaseClass:
    def __init__(self):
        self.simList = []
        self.varDisp = []
        self.randomizeSeeds = False
        self.executionModule = None
        self.simulationObject = None
        self.executionCount = 0
        self.retainSimulationData = False

    def setRandomizeSeeds(self, seedSet):
        self.randomizeSeeds = seedSet

    def setExecutionModule(self, newModule):
        self.executionModule = newModule

    def setSimulationObject(self, newObject):
        self.simulationObject = newObject

    def setExecutionCount(self, newCount):
        self.executionCount = newCount

    def setRetainSimulationData(self, retainData):
        self.retainSimulationData = retainData

    def addNewDispersion(self, disp):
        self.varDisp.append(disp)

    def executeSimulations(self):
        i = 0
        previousSimulation = None

        while i < self.executionCount:

            if previousSimulation is not None:
                previousSimulation.TotalSim.terminateSimulation()
            newSim = self.simulationObject

            for disp in self.varDisp:
                nextValue = disp.generate()
                if isinstance(nextValue, list):
                    for i in range(3):
                        execString = 'newSim.' + disp.varName + '[' + str(i) + '] = ' + str(nextValue[0])
                        exec(execString)
                else:
                    execString = 'newSim.' + disp.varName + ' = ' + str(nextValue)
                    exec(execString)

            self.executionModule(newSim)

            if self.retainSimulationData:
                self.simList.append(newSim)

            previousSimulation = newSim
            i += 1
            print i
