import numpy as np
from numpy import linalg as la
from numpy import sin, cos
np.set_printoptions(precision=12)
import sys, os, inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('ADCSAlgorithms')
sys.path.append(splitPath[0] + '/modules')
sys.path.append(splitPath[0] + '/PythonModules')
import RigidBodyKinematics as rbk
import astroFunctions as af

def normalize(v):
    norm=np.linalg.norm(v)
    if norm==0:
       return v
    return v/norm

def printResults_VelocityPoint(r_BN_N, v_BN_N, celBodyPosVec, celBodyVelVec, mu):
    r = r_BN_N - celBodyPosVec
    v = v_BN_N - celBodyVelVec
    h = np.cross(r, v)
    i_r = af.normalize(r)
    i_v = normalize(v)
    i_h = normalize(h)
    i_n = np.cross(i_v, i_h)
    VN = np.array([ i_n, i_v, i_h ])
    sigma_VN = rbk.C2MRP(VN)

    hm = la.norm(h)
    rm = la.norm(r)
    drdt = np.dot(v, i_r)
    dfdt = hm / (rm * rm)
    ddfdt2 = -2.0 * drdt / rm * dfdt

    (a, e, i, Omega, omega, f) = af.RV2OE(mu, r, v)
    den = 1 + e * e + 2 * e * cos(f)
    temp = e * (e + cos(f)) / den
    dBdt = temp * dfdt
    ddBdt2 = temp * ddfdt2 + (e * (e * e - 1) * sin(f)) / (den * den) * dfdt * dfdt

    omega_VN_N = (-dBdt + dfdt) * i_h
    domega_VN_N = (-ddBdt2 + ddfdt2) * i_h

    print 'sigma_VN = ', sigma_VN
    print 'omega_VN_N = ', omega_VN_N
    print 'domega_VN_N = ', domega_VN_N

    return (sigma_VN, omega_VN_N, domega_VN_N)

# MAIN
# Initial Conditions (IC)
MU_EARTH = 398600.436
r_BN_N = np.array([500., 500., 1000.])
v_BN_N = np.array([10., 10., 0.])
celBodyPosVec = np.array([-500., -500., 0.])
celBodyVelVec = np.array([0., 0., 0.])
# Print generated Velocity Frame for the given IC
printResults_VelocityPoint(r_BN_N, v_BN_N, celBodyPosVec, celBodyVelVec, MU_EARTH)