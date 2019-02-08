/*
 ISC License

 Copyright (c) 2016-2018, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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

#ifndef _HEADING_UKF_H_
#define _HEADING_UKF_H_

#include "messaging/static_messaging.h"
#include <stdint.h>
#include "simFswInterfaceMessages/navAttIntMsg.h"
#include "fswMessages/vehicleConfigFswMsg.h"
#include "fswMessages/headingFilterFswMsg.h"
#include "fswMessages/opnavFswMsg.h"


/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*!@brief Data structure for heading Switch unscented kalman filter estimator. Please see the _Documentation folder for details on how this Kalman Filter Functions.
 */
typedef struct {
    char navStateOutMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output message*/
    char filtDataOutMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output filter data message*/
    char opnavDataInMsgName[MAX_STAT_MSG_LENGTH];/*!< The name of the input opnav data message*/
    
	int numStates;                /*!< [-] Number of states for this filter*/
	int countHalfSPs;             /*!< [-] Number of sigma points over 2 */
	int numObs;                   /*!< [-] Number of measurements this cycle */
	double beta;                  /*!< [-] Beta parameter for filter */
	double alpha;                 /*!< [-] Alpha parameter for filter*/
	double kappa;                 /*!< [-] Kappa parameter for filter*/
	double lambdaVal;             /*!< [-] Lambda parameter for filter*/
	double gamma;                 /*!< [-] Gamma parameter for filter*/
    double qObsVal;               /*!< [-] OpNav instrument noise parameter*/

	double dt;                     /*!< [s] seconds since last data epoch */
	double timeTag;                /*!< [s]  Time tag for statecovar/etc */

    double bVec_B[HEAD_N_STATES];       /*!< [-] current vector of the b frame used to make frame */
    double switchTresh;             /*!< [-]  Threshold for switching frames */
    
    double stateInit[HEAD_N_STATES_SWITCH];    /*!< [-] State to initialize filter to*/
    double state[HEAD_N_STATES_SWITCH];        /*!< [-] State estimate for time TimeTag*/
    
	double wM[2 * HEAD_N_STATES_SWITCH + 1]; /*!< [-] Weighting vector for sigma points*/
	double wC[2 * HEAD_N_STATES_SWITCH + 1]; /*!< [-] Weighting vector for sigma points*/

	double sBar[HEAD_N_STATES_SWITCH*HEAD_N_STATES_SWITCH];         /*!< [-] Time updated covariance */
    double covarInit[HEAD_N_STATES_SWITCH*HEAD_N_STATES_SWITCH];        /*!< [-] covariance to init to*/
	double covar[HEAD_N_STATES_SWITCH*HEAD_N_STATES_SWITCH];        /*!< [-] covariance */
    double xBar[HEAD_N_STATES_SWITCH];            /*! [-] Current mean state estimate*/

	double obs[OPNAV_MEAS];          /*!< [-] Observation vector for frame*/
	double yMeas[OPNAV_MEAS*(2*HEAD_N_STATES_SWITCH+1)];        /*!< [-] Measurement model data */
    double postFits[OPNAV_MEAS];  /*!< [-] PostFit residuals */
    
	double SP[(2*HEAD_N_STATES_SWITCH+1)*HEAD_N_STATES_SWITCH];     /*!< [-]    sigma point matrix */

	double qNoise[HEAD_N_STATES_SWITCH*HEAD_N_STATES_SWITCH];       /*!< [-] process noise matrix */
	double sQnoise[HEAD_N_STATES_SWITCH*HEAD_N_STATES_SWITCH];      /*!< [-] cholesky of Qnoise */

	double qObs[OPNAV_MEAS*OPNAV_MEAS];  /*!< [-] Maximally sized obs noise matrix*/
    

    double sensorUseThresh;  /*!< -- Threshold below which we discount sensors*/
	NavAttIntMsg outputHeading;   /*!< -- Output heading estimate data */
    OpnavFswMsg opnavInBuffer;
    
    int32_t navStateOutMsgId;     /*!< -- ID for the outgoing body estimate message*/
    int32_t filtDataOutMsgId;   /*!< [-] ID for the filter data output message*/
    int32_t opnavDataInMsgId; 
}HeadingSuKFConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_headingSuKF(HeadingSuKFConfig *ConfigData, uint64_t moduleID);
    void CrossInit_headingSuKF(HeadingSuKFConfig *ConfigData, uint64_t moduleID);
    void Update_headingSuKF(HeadingSuKFConfig *ConfigData, uint64_t callTime,
        uint64_t moduleID);
	void Reset_headingSuKF(HeadingSuKFConfig *ConfigData, uint64_t callTime,
		uint64_t moduleID);
	void headingSuKFTimeUpdate(HeadingSuKFConfig *ConfigData, double updateTime);
    void headingSuKFMeasUpdate(HeadingSuKFConfig *ConfigData, double updateTime);
	void headingStateProp(double *stateInOut,  double *b_vec, double dt);
    void headingSuKFMeasModel(HeadingSuKFConfig *ConfigData);
    void headingSuKFComputeDCM_BS(double heading[HEAD_N_STATES], double bVec[HEAD_N_STATES], double *dcm);
    void headingSuKFSwitch(double *bVec_B, double *states, double *covar);

#ifdef __cplusplus
}
#endif

/*! @} */

#endif
