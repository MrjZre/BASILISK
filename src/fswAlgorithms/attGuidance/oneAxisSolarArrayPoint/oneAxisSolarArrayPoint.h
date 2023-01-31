/*
 ISC License

 Copyright (c) 2023, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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

#ifndef _THREE_AXIS_POINT_
#define _THREE_AXIS_POINT_

#include <stdint.h>
#include "architecture/utilities/bskLogging.h"
#include "cMsgCInterface/AttRefMsg_C.h"
#include "cMsgCInterface/BodyHeadingMsg_C.h"
#include "cMsgCInterface/InertialHeadingMsg_C.h"
#include "cMsgCInterface/NavTransMsg_C.h"
#include "cMsgCInterface/EphemerisMsg_C.h"
#include "cMsgCInterface/NavAttMsg_C.h"

#define EPS 1e-12

enum alignmentPriority{
    prioritizeAxisAlignment = 0,
    prioritizeSolarArrayAlignment = 1
};

enum bodyAxisInput{
    inputBodyHeadingParameter = 0,
    inputBodyHeadingMsg = 1
};

enum inertialAxisInput{
    inputInertialHeadingParameter = 0,
    inputInertialHeadingMsg = 1,
    inputEphemerisMsg = 2
};

/*! @brief Top level structure for the sub-module routines. */
typedef struct {

    /* declare these quantities that always must be specified as flight software parameters */
    double a1Hat_B[3];                           //!< arrays axis direction in B frame
    int alignmentPriority;                       //!< flag to indicate which constraint must be prioritized

    /* declare these optional quantities */
    double h1Hat_B[3];                           //!< main heading in B frame coordinates
    double h2Hat_B[3];                           //!< secondary heading in B frame coordinates
    double hHat_N[3];                            //!< main heading in N frame coordinates
    double a2Hat_B[3];                           //!< body frame heading that should remain as close as possible to Sun heading

    /* declare these internal variables that are used by the module and should not be declared by the user */
    int      bodyAxisInput;                      //!< flag variable to determine how the body axis input is specified 
    int      inertialAxisInput;                  //!< flag variable to determine how the inertial axis input is specified 
    int      count;                              //!< count variable used in the finite difference logic
    uint64_t T1NanoSeconds;                      //!< callTime one update step prior
    uint64_t T2NanoSeconds;                      //!< callTime two update steps prior
    double   sigma_RN_1[3];                      //!< reference attitude one update step prior
    double   sigma_RN_2[3];                      //!< reference attitude two update steps prior

    /* declare module IO interfaces */
    NavAttMsg_C          attNavInMsg;             //!< input msg measured attitude
    BodyHeadingMsg_C     bodyHeadingInMsg;        //!< input body heading msg
    InertialHeadingMsg_C inertialHeadingInMsg;    //!< input inertial heading msg
    NavTransMsg_C        transNavInMsg;           //!< input msg measured position
    EphemerisMsg_C       ephemerisInMsg;          //!< input ephemeris msg
    AttRefMsg_C          attRefOutMsg;            //!< output attitude reference message

    BSKLogger *bskLogger;                         //!< BSK Logging

}oneAxisSolarArrayPointConfig;

#ifdef __cplusplus
extern "C" {
#endif

    void SelfInit_oneAxisSolarArrayPoint(oneAxisSolarArrayPointConfig *configData, int64_t moduleID);
    void Reset_oneAxisSolarArrayPoint(oneAxisSolarArrayPointConfig *configData, uint64_t callTime, int64_t moduleID);
    void Update_oneAxisSolarArrayPoint(oneAxisSolarArrayPointConfig *configData, uint64_t callTime, int64_t moduleID);

#ifdef __cplusplus
}
#endif


#endif
