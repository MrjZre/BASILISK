/*
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

 */

#ifndef SIM_VSCMG_CONFIG_MESSAGE_H
#define SIM_VSCMG_CONFIG_MESSAGE_H

/*! @brief enumeration definiting the types of VSCMG modes */ 
enum VSCMGModels { vscmgBalancedWheels, vscmgJitterSimple, vscmgJitterFullyCoupled };


/*! @brief Structure used to define the individual VSCMG configuration data message*/
typedef struct {
	VSCMGModels VSCMGModel; //!< [-], Type of imbalance model to use
	Eigen::Vector3d rGB_B;		//!< [m], position vector of the VSCMG relative to the spacecraft body frame
	Eigen::Vector3d gsHat0_B;
	Eigen::Vector3d gsHat_B;	//!< [-] spin axis unit vector in body frame
	Eigen::Vector3d gtHat0_B;
	Eigen::Vector3d gtHat_B;
	Eigen::Vector3d ggHat_B;
	Eigen::Vector3d w2Hat0_B;	//!< [-] initial torque axis unit vector in body frame
	Eigen::Vector3d w2Hat_B;
    Eigen::Vector3d w3Hat0_B;	//!< [-] initial gimbal axis unit vector in body frame
	Eigen::Vector3d w3Hat_B;
    double massV;               //!< [kg]
	double massG;               //!< [kg]
	double massW;               //!< [kg]
    double theta;              //!< [rad], wheel angle
    double Omega;              //!< [rad/s], wheel speed
	double gamma;              //!< [s], gimbal angle
	double gammaDot;              //!< [rad/s], gimbal rate
    double IW1;                 //!< [kg-m^2], spin axis gsHat rotor moment of inertia
    double IW2;                 //!< [kg-m^2], gtHat axis rotor moment of inertia
    double IW3;                 //!< [kg-m^2], ggHat axis rotor moment of inertia
	double IW13;                	//!< [kg-m^2], x-z inertia of wheel about wheel center in wheel frame (imbalance)
	double IG1;              	//!< [kg-m^2]
	double IG2;          		//!< [kg-m^2]
	double IG3;                 //!< [kg-m^2]
	double IG12;             	//!< [kg-m^2]
	double IG13;         		//!< [kg-m^2]
	double IG23;                //!< [kg-m^2]
	double IV1;              	//!< [kg-m^2]
	double IV2;          		//!< [kg-m^2]
	double IV3;                 //!< [kg-m^2]
	double rhoG;
	double rhoW;
    double U_s;                //!< [kg-m], static imbalance
    double U_d;                //!< [kg-m^2], dynamic imbalance
	Eigen::Vector3d rGcG_G;
    double d;                	//!< [m], wheel center of mass offset from wheel frame origin
	double l;
	double L;
    double u_s_current;          //!< [N-m], current motor torque
    double u_s_max;              //!< [N-m], Max torque
    double u_s_min;              //!< [N-m], Min torque
    double u_s_f;                //!< [N-m], Coulomb friction torque magnitude
    double Omega_max;          //!< [rad/s], max wheel speed
	double wheelLinearFrictionRatio;//!< [%] ratio relative to max speed value up to which the friction behaves linearly
	double u_g_current;          //!< [N-m], current motor torque
	double u_g_max;              //!< [N-m], Max torque
	double u_g_min;              //!< [N-m], Min torque
	double u_g_f;                //!< [N-m], Coulomb friction torque magnitude
	double gammaDot_max;          //!< [rad/s], max wheel speed
	double gimbalLinearFrictionRatio;//!< [%] ratio relative to max speed value up to which the friction behaves linearly

	Eigen::Matrix3d IGPntGc_B;
    Eigen::Matrix3d IWPntWc_B;
	Eigen::Matrix3d IPrimeGPntGc_B;
	Eigen::Matrix3d IPrimeWPntWc_B;
	Eigen::Vector3d rGcG_B;
	Eigen::Vector3d rGcB_B;
    Eigen::Vector3d rWcB_B;
	Eigen::Vector3d rWcG_B;
	Eigen::Matrix3d rTildeGcB_B;
    Eigen::Matrix3d rTildeWcB_B;
	Eigen::Vector3d rPrimeGcB_B;
    Eigen::Vector3d rPrimeWcB_B;
	Eigen::Matrix3d rPrimeTildeGcB_B;
	Eigen::Matrix3d rPrimeTildeWcB_B;

	Eigen::Vector3d aOmega; //!< [-], parameter used in coupled jitter back substitution
	Eigen::Vector3d bOmega; //!< [-], parameter used in coupled jitter back substitution
	double cOmega; //!< [-], parameter used in coupled jitter back substitution
	double dOmega;
	double eOmega;
	Eigen::Vector3d agamma;
	Eigen::Vector3d bgamma;
	double cgamma;
	double dgamma;
	double egamma;
	Eigen::Vector3d p;
	Eigen::Vector3d q;
	double s;

	double gravityTorqueWheel_s;
	double gravityTorqueGimbal_g;
}VSCMGConfigSimMsg;




#endif
