/*
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

*/

#ifndef COARSE_SUN_SENSOR_H
#define COARSE_SUN_SENSOR_H

#include <vector>
#include "utilities/sys_model.h"
#include "environment/spice/spice_interface.h"
#include "utilities/dyn_effector.h"
#include <random>

typedef enum {
    CSSFAULT_OFF,           /*!< CSS measurement is set to 0 for all future time
                             */
    CSSFAULT_STUCK_CURRENT, /*!< CSS measurement is set to current value for all future time */
    CSSFAULT_STUCK_MAX,     /*!< CSS measurement is set to maximum value for all future time */
    CSSFAULT_STUCK_RAND,    /*!< CSS measurement is set to randomly selected value for all future time */
    CSSFAULT_STUCK,         /*!< CSS measurement is set to percent value for all future time */
    CSSFAULT_RAND,          /*!< CSS measurement returns uniformly distributed random values between 0 and max */
    MAX_CSSFAULT
} CSSFaultState_t;

typedef struct {
    double OutputData;       /*!< CSS measurement output */
}CSSOutputData;

class CoarseSunSensor: public SysModel {
public:
    CoarseSunSensor();
    ~CoarseSunSensor();
    
    void CrossInit();
    void SelfInit();
    bool LinkMessages();
    void UpdateState(uint64_t CurrentSimNanos);
    void readInputMessages();
    void writeOutputMessages(uint64_t Clock);
    void setUnitDirectionVectorWithPerturbation(double cssThetaPerturb, double cssPhiPerturb);
    void setStructureToPlatformDCM(double yaw, double pitch, double roll);
    bool spacecraftIlluminated();
    void computeSunData();
    void computeTruthOutput();
    void applySensorErrors();
    void scaleActualOutput();
    
public:
    std::string InputSunMsg;                    /*!< Message name for sun data */
    std::string InputStateMsg;                  /*!< Message name for spacecraft state */
    std::string OutputDataMsg;                  /*!< Message name for CSS output data */
    CSSFaultState_t     faultState;             /*!< Specification used if state is set to COMPONENT_FAULT */
    double              stuckPercent;           /*!< percent of full value the CSS will remain stuck at if a fault is triggered */
    double              theta;                  /*!< rad, css azimuth angle, measured positive from the body +x axis around the +z axis */
    double              phi;                    /*!< rad, css elevation angle, measured positive toward the body +z axis from the x-y plane */
    double              B2P321Angles[3];
    double              PB[3][3];               /*!< DCM from platform frame P to body frame B */
    double              nHatStr[3];             /*!< css unit direction vector in structural components */
    double              sHatStr[3];             /*!< unit vector to sun in str */
    double              horizonPlane[3];        /*!< unit direction vector defining horizon cut off plane of CSS */
    double              directValue;            /*!< direct solar irradiance measurement */
    double              albedoValue;            /*!< albedo irradiance measurement */
    double              scaleFactor;            /*!< scale factor applied to sensor (common + individual multipliers) */
    double              trueValue;              /*!< total measurement without including perturbations */
    double              sensedValue;            /*!< total measurement including perturbations */
    double              outputValue;            /*!< output value to be scaled */
    double              ScaledValue;            /*!< Scaled value prior to discretization*/
    double              KellyFactor;            /*!< Kelly curve fit for output cosine curve*/
    double              fov;                    /*!< rad, field of view half angle */
    double              maxVoltage;             /*!< max voltage measurable by CSS, used in discretization */
    double              r_B[3];
    bool                MessagesLinked;             /*!< Indicator for whether inputs bound */
    double              SenBias;                    /*!< Sensor bias value */
    double              SenNoiseStd;                /*!< Sensor noise value */
    uint64_t            OutputBufferCount;          /*!< number of output msgs stored */
    bool                isOutputtingMeasured;       /*!< Flag indicating whether the output information is the truth or is the measured (corrupted with errors) */
private:
    int64_t InputSunID;                     /*!<  Connect to input time message */
    int64_t InputStateID;                   /*!<  Connect to input time message */
    int64_t OutputDataID;                   /*!<  Connect to output CSS data */
    SpicePlanetState SunData;               /*!<  Unused for now, but including it for future */
    OutputStateData StateCurrent;           /*!< Current SSBI-relative state */
    std::default_random_engine rgen;        /*!<  Random number generator for disp */
    std::normal_distribution<double> rnum;  /*!<  Random number distribution */
};

#endif
