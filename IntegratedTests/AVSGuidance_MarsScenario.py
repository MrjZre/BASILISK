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
import sys, os, inspect

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
sys.path.append(path + '/../PythonModules/')
import AVSSim
import matplotlib.pyplot as plt
#plt.rcParams.bbox_inches="tight"
from mpl_toolkits.mplot3d import Axes3D
import ctypes
import math
import MessagingAccess
import SimulationBaseClass
import sim_model
import logging
import numpy as np
from numpy import cos, sin
from numpy import linalg as la
import macros as mc
import astroFunctions as af
import RigidBodyKinematics as rbk


# ------------------- PLOTS DIRECTORY ------------------- #
paperPath = '/Users/marcolsmargenet/Desktop/AIAApaper/Figures/'
arePlotsSaved = False
if arePlotsSaved:
    plt.rcParams['figure.figsize'] = 2.5, 2.
    plt.rcParams.update({'font.size': 9})

# ------------------- PLOTTING FUNCTIONS ------------------- #

def plotRV_mag(r_BN_N, v_BN_N):
    t = r_BN_N[:, 0]
    print 'r_BN_0 = ', r_BN_N[0, 1:]
    print 'v_BN_0 = ', v_BN_N[0, 1:]
    r = np.array([])
    v = np.array([])
    for i in range(len(t)):
        r = np.append(r, la.norm(r_BN_N[i, 1:]))
        v = np.append(v, la.norm(v_BN_N[i, 1:]))
    print 'R_mag = ', r
    print 'V_mag = ', v
    print 'Initial Pos Vec: ', r_BN_N[0,:]
    print 'Final Pos Vec: ', r_BN_N[len(t)-1,:]
    print '\n'

    plt.figure(0)
    plt.plot(t * 1E-9, r * 1E-3, 'b')
    plt.title('Pos Mag [km]')

    plt.figure(1)
    plt.plot(t * 1E-9, v * 1E-3, 'g')
    plt.title('Vel Mag [km]')
    plt.figure(2)
    plt.plot(t * 1E-9, r, 'b', t * 1E-9, v, 'g')
    plt.legend(['Pos Mag [km]', 'Vel Mag [km/s]'])

def plotRotNav(sigma_BN, omega_BN_B):
    print 'sigma_BN = ', sigma_BN[:, 1:]
    print 'omega_BN_N = ', omega_BN_B[:, 1:]
    print '\n'

    plt.figure(5)
    plt.ylim([-1.0, 1.0])
    plt.plot(sigma_BN[:, 0] * 1E-9, sigma_BN[:, 1]
             , sigma_BN[:, 0] * 1E-9, sigma_BN[:, 2]
             , sigma_BN[:, 0] * 1E-9, sigma_BN[:, 3])
    plt.legend(['$x_1$', '$x_2$', '$x_3$'])
    plt.title(TheAVSSim.modeRequest + ': $\sigma_{BN}$')
    plt.figure(6)
    plt.plot(omega_BN_B[:, 0] * 1E-9, omega_BN_B[:, 1]
             , omega_BN_B[:, 0] * 1E-9, omega_BN_B[:, 2]
             , omega_BN_B[:, 0] * 1E-9, omega_BN_B[:, 3])
    plt.legend(['$x_1$', '$x_2$', '$x_3$'])
    plt.title(TheAVSSim.modeRequest + ': $\omega_{BN, B}$')

def plotReference(sigma_RN, omega_RN_N):
    print 'sigma_RN = ', sigma_RN[:, 1:]
    print 'omega_RN_N = ', omega_RN_N[:, 1:]
    print '\n'

    plt.figure(10)
    plt.ylim([-1.0, 1.0])
    plt.plot(sigma_RN[:, 0] * 1E-9, sigma_RN[:, 1]
             , sigma_RN[:, 0] * 1E-9, sigma_RN[:, 2]
             , sigma_RN[:, 0] * 1E-9, sigma_RN[:, 3])

    plt.legend(['$\sigma_1$', '$\sigma_2$', '$\sigma_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\sigma_{RN}$')
    if arePlotsSaved:
        plt.savefig(paperPath + TheAVSSim.modeRequest + "/sigma_RN.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': Reference Att $\sigma_{RN}$')

    plt.figure(11)
    plt.plot(omega_RN_N[:, 0] * 1E-9, omega_RN_N[:, 1]
             , omega_RN_N[:, 0] * 1E-9, omega_RN_N[:, 2]
             , omega_RN_N[:, 0] * 1E-9, omega_RN_N[:, 3])
    plt.legend(['$\omega_1$', '$\omega_2$', '$\omega_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\omega_{RN}$ [rad/s]')
    if arePlotsSaved:
        plt.savefig(paperPath + TheAVSSim.modeRequest + "/omega_RN_N.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ' : Reference Rate $\omega_{RN}$')

def plotBaseReference(sigma_R0N, omega_R0N_N):
    print 'sigma_R0N = ', sigma_R0N[:, 1:]
    print 'omega_R0N_N = ', omega_R0N_N[:, 1:]
    print '\n'

    plt.figure(15)
    plt.ylim([-1.0, 1.0])
    plt.plot(sigma_R0N[:, 0] * 1E-9, sigma_R0N[:, 1]
             , sigma_R0N[:, 0] * 1E-9, sigma_R0N[:, 2]
             , sigma_R0N[:, 0] * 1E-9, sigma_R0N[:, 3])
    plt.legend(['$\sigma_1$', '$\sigma_2$', '$\sigma_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\sigma_{R0N}$')
    if arePlotsSaved:
        plt.savefig(paperPath + TheAVSSim.modeRequest + "/sigma_R0N.pdf", bbox_inches='tight')
    else:
        plt.title(': Base Reference Att $\sigma_{R0N}$')
    plt.figure(16)
    plt.plot(omega_R0N_N[:, 0] * 1E-9, omega_R0N_N[:, 1]
             , omega_R0N_N[:, 0] * 1E-9, omega_R0N_N[:, 2]
             , omega_R0N_N[:, 0] * 1E-9, omega_R0N_N[:, 3])
    plt.legend(['$\omega_1$', '$\omega_2$', '$\omega_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\omega_{R0N}$ [rad/s]')
    if arePlotsSaved:
        plt.savefig(paperPath + TheAVSSim.modeRequest + "/omega_R0N_N.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest +': Base Reference Rate $\omega_{R0/N}$')

def plotEulerRates(eulerRates):
    print 'eulerRates = ', eulerRates[:, 1:]
    print '\n'
    t_vec = eulerRates[:, 0]
    psiDot_vec = eulerRates[:, 1]
    thetaDot_vec = eulerRates[:, 2]
    phiDot_vec = eulerRates[:, 3]
    plt.figure(20)
    plt.plot(t_vec * 1E-9, psiDot_vec
             , t_vec * 1E-9, thetaDot_vec
             , t_vec * 1E-9, phiDot_vec)
    plt.legend(['$\dot\psi$', '$\dot\Theta$', '$\dot\phi$'])
    plt.xlabel('time [s]')
    plt.ylabel('3-2-1 Euler Rates [rad/s]')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+"/euler_rates.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': 3-2-1 Euler Rates wrt Base Ref')


def plotEulerSet(eulerSet):
    print 'eulerSet = ', eulerSet[:, 1:]
    print '\n'
    t_vec = eulerSet[:, 0]
    psi_vec = eulerSet[:, 1]
    theta_vec = eulerSet[:, 2]
    phi_vec = eulerSet[:, 3]
    plt.figure(21)
    plt.plot(t_vec * 1E-9, psi_vec
             , t_vec * 1E-9, theta_vec
             , t_vec * 1E-9, phi_vec)
    plt.legend(['$\psi$', '$\Theta$', '$\phi$'])
    plt.xlabel('time [s]')
    plt.ylabel('3-2-1 Euler Set [rad]')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+"/euler_set.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': 3-2-1 Euler Set wrt Base Ref')

    rx_vec = np.array([])
    ry_vec = np.array([])
    rz_vec = np.array([])
    for i in range(len(t_vec)):
        rx = cos(theta_vec[i]) * cos(psi_vec[i])
        ry = cos(theta_vec[i]) * sin(psi_vec[i])
        rz = sin(theta_vec[i])
        rx_vec = np.append(rx_vec, rx)
        ry_vec = np.append(ry_vec, ry)
        rz_vec = np.append(rz_vec, rz)
    def plot_boresightXZ():
        plt.figure(22)
        plt.plot(rx_vec, rz_vec)
        plt.xlabel('$R_X$')
        plt.ylabel('$R_Z$')
        if arePlotsSaved:
            plt.savefig(paperPath+TheAVSSim.modeRequest+"/boresight_XZ.pdf", bbox_inches='tight')
        else:
            plt.title(TheAVSSim.modeRequest + ': bore-sight: XZ-plane')
    def plot_boresightYZ():
        plt.figure(23)
        plt.plot(ry_vec, rz_vec)
        plt.xlabel('$R_Y$')
        plt.ylabel('$R_Z$')
        if arePlotsSaved:
            plt.savefig(paperPath+TheAVSSim.modeRequest+"/boresight_YZ.pdf", bbox_inches='tight')
        else:
            plt.title(TheAVSSim.modeRequest + ': bore-sight: YZ-plane')
    def plot_boresight3D():
        fig = plt.figure(24, figsize=(5,4))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(rx_vec, ry_vec, rz_vec)
        max_range = np.array([rx_vec.max() - rx_vec.min(), ry_vec.max() - ry_vec.min(), rz_vec.max() - rz_vec.min()]).max()
        Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (rx_vec.max() + rx_vec.min())
        Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (ry_vec.max() + ry_vec.min())
        Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (rz_vec.max() + rz_vec.min())
        for xb, yb, zb in zip(Xb, Yb, Zb):
            ax.plot([xb], [yb], [zb], 'w')
        ax.scatter(0, 0, 0)
        if arePlotsSaved:
            plt.savefig(paperPath+TheAVSSim.modeRequest+"/boresight_3D.pdf", bbox_inches='tight')
        else:
            plt.title(TheAVSSim.modeRequest + ': bore-sight: 3D')
    plot_boresightXZ()
    plot_boresightYZ()
    plot_boresight3D()


def plotTrueBodyEulerSet(sigma_BN):
    rx_vec = np.array([])
    ry_vec = np.array([])
    rz_vec = np.array([])
    t = sigma_BN[:, 0] * 1E-9
    for i in range(len(t)):
        if t[i] > 500:
            e = rbk.MRP2Euler321(sigma_BN[i, 1:])
            rx = cos(e[1]) * cos(e[0])
            ry = cos(e[1]) * sin(e[0])
            rz = sin(e[1])
            rx_vec = np.append(rx_vec, rx)
            ry_vec = np.append(ry_vec, ry)
            rz_vec = np.append(rz_vec, rz)
    fig = plt.figure(100)
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(rx_vec, ry_vec, rz_vec)
    max_range = np.array([rx_vec.max() - rx_vec.min(), ry_vec.max() - ry_vec.min(), rz_vec.max() - rz_vec.min()]).max()
    Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][0].flatten() + 0.5 * (rx_vec.max() + rx_vec.min())
    Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][1].flatten() + 0.5 * (ry_vec.max() + ry_vec.min())
    Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2, -1:2:2][2].flatten() + 0.5 * (rz_vec.max() + rz_vec.min())
    for xb, yb, zb in zip(Xb, Yb, Zb):
        ax.plot([xb], [yb], [zb], 'w')
    ax.scatter(0, 0, 0)
    plt.title(' Real Body Bore-sight Pointing')




def plotTrackingError(sigma_BR, omega_BR_B):
    print 'sigma_BR = ', sigma_BR[:, 1:]
    print 'omega_BR_B = ', omega_BR_B[:, 1:]
    print '\n'

    plt.figure(30)
    plt.plot(sigma_BR[:, 0] * 1E-9, sigma_BR[:, 1]
             , sigma_BR[:, 0] * 1E-9, sigma_BR[:, 2]
             ,sigma_BR[:, 0] * 1E-9, sigma_BR[:, 3])
    #plt.ylim([-1.0, 1.0])
    plt.legend(['$\sigma_1$', '$\sigma_2$', '$\sigma_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\sigma_{BR}$')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+"/sigma_BR.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': Att Tracking Error $\sigma_{BR}$')

    plt.figure(31)
    plt.plot(omega_BR_B[:, 0] * 1E-9, omega_BR_B[:, 1]
             , omega_BR_B[:, 0] * 1E-9, omega_BR_B[:, 2]
             , omega_BR_B[:, 0] * 1E-9, omega_BR_B[:, 3])
    plt.legend(['$\omega_1$', '$\omega_2$', '$\omega_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('$\omega_{BR}$ [rad/s]')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+'/omega_BR_B.pdf', bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': Rate Tracking Error $\omega_{BR, B}$')

    plt.figure(32)
    t = sigma_BR[:, 0] * 1E-9
    eps1 = np.array([])
    eps2 = np.array([])
    eps3 = np.array([])
    for i in range(len(t)):
        e1 = np.sqrt(sigma_BR[i, 1] * sigma_BR[i, 1] + omega_BR_B[i, 1] * omega_BR_B[i, 1])
        e2 = np.sqrt(sigma_BR[i, 2] * sigma_BR[i, 2] + omega_BR_B[i, 2] * omega_BR_B[i, 2])
        e3 = np.sqrt(sigma_BR[i, 3] * sigma_BR[i, 3] + omega_BR_B[i, 3] * omega_BR_B[i, 3])
        eps1 = np.append(eps1, e1)
        eps2 = np.append(eps2, e2)
        eps3 = np.append(eps3, e3)
    plt.semilogy(t, eps1, t, eps2, t, eps3)
    plt.legend(['$\epsilon_1$', '$\epsilon_2$', '$\epsilon_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('log($\epsilon$)')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+"/error.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': Average Error $\epsilon_i$')


def plotControlTorque(Lr):
    print 'Lr = ', Lr[:, 1:]
    print '\n'

    plt.figure(40)
    plt.plot(Lr[:, 0] * 1E-9, Lr[:, 1]
             , Lr[:, 0] * 1E-9, Lr[:, 2]
             ,Lr[:, 0] * 1E-9, Lr[:, 3])
    plt.legend(['$u_1$', '$u_2$', '$u_3$'])
    plt.xlabel('time [s]')
    plt.ylabel('Control torque [N m]')
    if arePlotsSaved:
        plt.savefig(paperPath+TheAVSSim.modeRequest+"/torque.pdf", bbox_inches='tight')
    else:
        plt.title(TheAVSSim.modeRequest + ': Torque $L_r$')


# ------------------- SUPPORT METHODS------------------- #
# MRP Feedback gains
def computeDiscriminant(K, P, I):
    d = np.array([])
    for I_i in I:
        d = np.append(d, -K * I_i + P * P)
    return d
def computeGains(P, I):
    K = np.array([])
    for i in range(3):
        K = np.append(K, P * P / I[i])
    K_cr = max(K)
    return K_cr


# ------------------- MAIN ------------------- #

def executeGuidance(TheAVSSim):
    def doubleTest(mode1, mode2):
        TheAVSSim.modeRequest = mode1
        print '\n Mode Request = ', TheAVSSim.modeRequest
        TheAVSSim.ConfigureStopTime(int(60 * 20 * 1E9))
        TheAVSSim.ExecuteSimulation()

        TheAVSSim.modeRequest = mode2
        print '\n Mode Request = ', TheAVSSim.modeRequest
        TheAVSSim.ConfigureStopTime(int(60 * 40 * 1E9)) # 60 * 20 * 8 * 1E9
        TheAVSSim.ExecuteSimulation()

    def singleTest(mode):
        TheAVSSim.modeRequest = mode
        print '\n Mode Request = ', TheAVSSim.modeRequest
        TheAVSSim.ConfigureStopTime(int(60 * 20 * 4 * 1E9))
        TheAVSSim.ExecuteSimulation()


    # STAND-ALONE HILL POINT:
    #TheAVSSim.hillPointData.outputDataName = "att_ref_output"

    # STAND-ALONE INERTIAL 3D POINT:
    #TheAVSSim.inertial3DData.outputDataName = "att_ref_output"

    # VELOCITY POINT:
    TheAVSSim.velocityPointData.mu = TheAVSSim.VehOrbElemObject.mu

    # CEL2BDY POINT:
    TheAVSSim.celTwoBodyPointData.inputCelMessName = "mars_display_frame_data"
    #TheAVSSim.celTwoBodyPointData.inputSecMessName = "sun_display_frame_data"

    # EULER ANGLE ROTATION (FOR ORBIT AXIS SPIN)
    # angleRates = np.array([0.0, 0.0, 0.2]) * mc.D2R
    # SimulationBaseClass.SetCArray(angleRates, 'double', TheAVSSim.eulerRotationData.angleRates)

    # RASTER MNVR
    TheAVSSim.eulerRotationData.inputEulerSetName = "euler_angle_set"
    TheAVSSim.eulerRotationData.inputEulerRatesName = "euler_angle_rates"

    # ATT TRACKING ERROR
    angleOff = np.pi
    R0R = rbk.Mi(angleOff, 3)
    sigma_R0R = rbk.C2MRP(R0R)
    #SimulationBaseClass.SetCArray(sigma_R0R, 'double', TheAVSSim.attTrackingErrorData.sigma_R0R)

    # DEAD-BAND
    #TheAVSSim.MRP_SteeringRWAData.inputGuidName = "db_att_guid_out"

    # MRP FEEDBACK GAINS
    P = 40.
    I_vec = ctypes.cast(TheAVSSim.LocalConfigData.I.__long__(), ctypes.POINTER(ctypes.c_double))
    I = np.array([I_vec[0], I_vec[4], I_vec[8]])
    K = computeGains(P, I) * 8.
    print 'K = ', K
    d = computeDiscriminant(K, P, I)
    print 'Discriminant = ', d
    TheAVSSim.MRP_FeedbackRWAData.K = K
    TheAVSSim.MRP_FeedbackRWAData.P = P

    # VISUALIZATION
    #TheAVSSim.isUsingVisualization = True
    #TheAVSSim.clockSynchData.accelFactor = 20.0 * 1.5

    # INIT SIM:
    TheAVSSim.InitializeSimulation()
    TheAVSSim.ConfigureStopTime(int(1 * 1E9))
    TheAVSSim.ExecuteSimulation()

    # GUIDANCE PROFILES
    #singleTest('inertial3DPoint')
    #doubleTest('inertial3DPoint', 'inertial3DSpin')
    #singleTest('hillPoint')
    #singleTest('velocityPoint')
    #doubleTest('hillPoint', 'velocityPoint')
    #singleTest('celTwoBodyPoint')
    #doubleTest('velocityPoint', 'celTwoBodyPoint')
    #singleTest('inertial3DSpin')
    #singleTest('eulerRotation')
    singleTest('rasterMnvr')
    #singleTest('deadbandGuid')

if __name__ == "__main__":
    TheAVSSim = AVSSim.AVSSim()
    TheAVSSim.TotalSim.logThisMessage("controlTorqueRaw", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("att_ref_output_stage1", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("simple_nav_output", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("att_ref_output", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("nom_att_guid_out", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("db_att_guid_out", int(1E9))
    TheAVSSim.AddVariableForLogging('errorDeadband.error', int(1E9))
    TheAVSSim.AddVariableForLogging('errorDeadband.boolWasControlOff', int(1E9))
    TheAVSSim.TotalSim.logThisMessage("euler_set_output", int(1E9))
    TheAVSSim.TotalSim.logThisMessage("euler_rates_output", int(1E9))

    TheAVSSim.VehDynObject.GravData[0].IsCentralBody = False
    TheAVSSim.VehDynObject.GravData[0].IsDisplayBody = False
    TheAVSSim.VehDynObject.GravData[2].IsCentralBody = True
    TheAVSSim.VehDynObject.GravData[2].IsDisplayBody = True
    TheAVSSim.SpiceObject.zeroBase = "mars"
    TheAVSSim.SpiceObject.referenceBase = "MARSIAU"
    TheAVSSim.VehOrbElemObject.mu = TheAVSSim.MarsGravBody.mu

    TheAVSSim.VehOrbElemObject.CurrentElem.a = af.M_radius * 4 * 1000.0
    TheAVSSim.VehOrbElemObject.CurrentElem.e = 0.7
    TheAVSSim.VehOrbElemObject.CurrentElem.i = 0.0 * math.pi / 180.0
    TheAVSSim.VehOrbElemObject.CurrentElem.Omega = 0.0
    TheAVSSim.VehOrbElemObject.CurrentElem.omega = 0.0
    TheAVSSim.VehOrbElemObject.CurrentElem.f = 170.0 * math.pi / 180.0

    # Convert those OEs to cartesian
    TheAVSSim.VehOrbElemObject.Elements2Cartesian()
    PosVec = ctypes.cast(TheAVSSim.VehOrbElemObject.r_N.__long__(),
                         ctypes.POINTER(ctypes.c_double))
    VelVec = ctypes.cast(TheAVSSim.VehOrbElemObject.v_N.__long__(),
                         ctypes.POINTER(ctypes.c_double))
    TheAVSSim.VehDynObject.PositionInit = sim_model.DoubleVector([PosVec[0], PosVec[1], PosVec[2]])
    TheAVSSim.VehDynObject.VelocityInit = sim_model.DoubleVector([VelVec[0], VelVec[1], VelVec[2]])

    print 'r0 = [', PosVec[0], ', ', PosVec[1], ', ', PosVec[2], ']'
    print 'v0 = [', VelVec[0], ', ', VelVec[1], ', ', VelVec[2], ']'
    executeGuidance(TheAVSSim)

    P = af.orbitalPeriod(TheAVSSim.VehOrbElemObject.CurrentElem.a, TheAVSSim.VehOrbElemObject.mu)
    n = 2 * np.pi / P
    print '\n'
    print 'Orbital Period [days] = ', P * af.SEC2DAY
    print 'Orbital Mean Motion [rad/s]', n
    print 'Mars Orbit Eccentricity = ', TheAVSSim.VehOrbElemObject.CurrentElem.e
    print 'Mars Orbit Inclination = ', TheAVSSim.VehOrbElemObject.CurrentElem.i
    print '\n'

    r_BN_N = TheAVSSim.pullMessageLogData("simple_nav_output.r_BN_N", range(3))
    v_BN_N = TheAVSSim.pullMessageLogData("simple_nav_output.v_BN_N", range(3))
    #plotRV_mag(r_BN_N, v_BN_N)

    sigma_BN = TheAVSSim.pullMessageLogData("simple_nav_output.sigma_BN", range(3))
    omega_BN_B = TheAVSSim.pullMessageLogData("simple_nav_output.omega_BN_B", range(3))
    #plotRotNav(sigma_BN, omega_BN_B)
    if TheAVSSim.modeRequest == 'rasterMnvr':
        plotTrueBodyEulerSet(sigma_BN)


    sigma_RN = TheAVSSim.pullMessageLogData("att_ref_output.sigma_RN", range(3))
    omega_RN_N = TheAVSSim.pullMessageLogData("att_ref_output.omega_RN_N", range(3))
    domega_RN_N = TheAVSSim.pullMessageLogData("att_ref_output.domega_RN_N", range(3))
    #plotReference(sigma_RN, omega_RN_N)

    if TheAVSSim.modeRequest =='eulerRotation' or TheAVSSim.modeRequest == 'rasterMnvr':
        euler123set = TheAVSSim.pullMessageLogData("euler_set_output.set", range(3))
        euler123rates = TheAVSSim.pullMessageLogData("euler_rates_output.set", range(3))
        plotEulerSet(euler123set)
        plotEulerRates(euler123rates)

    if (TheAVSSim.modeRequest == 'rasterMnvr'
        or TheAVSSim.modeRequest =='eulerRotation'
        or TheAVSSim.modeRequest =='inertial3DSpin'):
        sigma_R0N = TheAVSSim.pullMessageLogData("att_ref_output_stage1.sigma_RN", range(3))
        omega_R0N_N = TheAVSSim.pullMessageLogData("att_ref_output_stage1.omega_RN_N", range(3))
        domega_R0N_N = TheAVSSim.pullMessageLogData("att_ref_output_stage1.domega_RN_N", range(3))
        #plotBaseReference(sigma_R0N, omega_R0N_N)


    if (TheAVSSim.modeRequest == 'deadbandGuid'):
        sigma_BR = TheAVSSim.pullMessageLogData("db_att_guid_out.sigma_BR", range(3))
        omega_BR_B = TheAVSSim.pullMessageLogData("db_att_guid_out.omega_BR_B", range(3))
        plotTrackingError(sigma_BR, omega_BR_B)

        dbError = TheAVSSim.GetLogVariableData('errorDeadband.error')
        boolControlOff = TheAVSSim.GetLogVariableData('errorDeadband.boolWasControlOff')
        print 'Control OFF? = ', boolControlOff[:, 1]
        plt.figure(200)
        plt.plot(dbError[:, 0] * 1.0E-9, dbError[:, 1], 'b')
        plt.axhline(TheAVSSim.errorDeadbandData.innerThresh, color='green')
        plt.axhline(TheAVSSim.errorDeadbandData.outerThresh, color='red')
        plt.plot(boolControlOff[:, 0] * 1.0E-9, boolControlOff[:, 1], 'magenta')
        plt.ylim([-0.02, 1.5])
        plt.legend(['error', 'inner thresh', 'outer thresh', 'control (0=ON, 1=OFF)'])
        plt.title('Deadband Mode')

    else:
        sigma_BR = TheAVSSim.pullMessageLogData("nom_att_guid_out.sigma_BR", range(3))
        omega_BR_B = TheAVSSim.pullMessageLogData("nom_att_guid_out.omega_BR_B", range(3))
        omega_RN_B = TheAVSSim.pullMessageLogData("nom_att_guid_out.omega_RN_B", range(3))
        domega_RN_B = TheAVSSim.pullMessageLogData("nom_att_guid_out.domega_RN_B", range(3))
        plotTrackingError(sigma_BR, omega_BR_B)

    Lr = TheAVSSim.pullMessageLogData("controlTorqueRaw.torqueRequestBody", range(3))
    #plotControlTorque(Lr)

    plt.show()