/*
 ISC License
 
 Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder
 
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

#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "biasODuKF.h"
#include "../_GeneralModuleFiles/ukfUtilities.h"

/*! This method creates the two moduel output messages.
 @return void
 @param configData The configuration data associated with the OD filter
 */
void SelfInit_biasODuKF(BiasODuKFConfig *configData, uint64_t moduleId)
{
    /*! - Create a navigation message to be used for control */
    configData->biasStateOutMsgId = CreateNewMessage(configData->biasStateOutMsgName,
                                                    sizeof(BiasOpNavMsg), "BiasOpNavMsg", moduleId);
    /*! - Create filter states output message for filter states, covariance, postfits, and debugging*/
    configData->biasFiltOutMsgId = CreateNewMessage(configData->biasFiltOutMsgName,
                                                    sizeof(BiasOpNavFilterMsg), "BiasOpNavFilterMsg", moduleId);
    
}

/*! This method performs the second stage of initialization for the OD filter.  It's primary function is to link the input messages that were created elsewhere.
 @return void
 @param configData The configuration data associated with the OD filter
 */
void CrossInit_biasODuKF(BiasODuKFConfig *configData, uint64_t moduleId)
{
    /*! Read in the treated position measurement from pixelLineConverter */
    configData->opNavInMsgId = subscribeToMessage(configData->opNavInMsgName, sizeof(OpNavFswMsg), moduleId);
    /*! Read in the raw position measurement from the filter */
    configData->navInMsgId = subscribeToMessage(configData->navInMsgName, sizeof(NavTransIntMsg), moduleId);
    /*! Read in the camera config */
    configData->cameraConfigMsgID = subscribeToMessage(configData->cameraConfigMsgName, sizeof(CameraConfigMsg), moduleId);
    /*! Read in hough Cirlces */
    configData->circlesInMsgID = subscribeToMessage(configData->circlesInMsgName, sizeof(CirclesOpNavMsg), moduleId);
    /*! Read in the Attitude from ST */
configData->attInMsgID = subscribeToMessage(configData->attInMsgName, sizeof(NavAttIntMsg), moduleId);
    
}

/*! This method resets the relative OD filter to an initial state and
 initializes the internal estimation matrices.
 @return void
 @param configData The configuration data associated with the OD filter
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Reset_biasODuKF(BiasODuKFConfig *configData, uint64_t callTime,
                       uint64_t moduleId)
{
    
    int32_t i;
    int32_t badUpdate=0; /* Negative badUpdate is faulty, */
    double tempMatrix[ODUKF_N_STATES_B*ODUKF_N_STATES_B];
    
    /*! - Initialize filter parameters to max values */
    configData->timeTag = callTime*NANO2SEC;
    configData->dt = 0.0;
    configData->numStates = ODUKF_N_STATES_B;
    configData->countHalfSPs = ODUKF_N_STATES_B;
    configData->numObs = ODUKF_N_MEAS;
    configData->firstPassComplete = 0;
    configData->planetId = configData->planetIdInit;
    
    /*! - Ensure that all internal filter matrices are zeroed*/
    vSetZero(configData->obs, configData->numObs);
    vSetZero(configData->wM, configData->countHalfSPs * 2 + 1);
    vSetZero(configData->wC, configData->countHalfSPs * 2 + 1);
    mSetZero(configData->sBar, configData->numStates, configData->numStates);
    mSetZero(configData->SP, configData->countHalfSPs * 2 + 1,
             configData->numStates);
    mSetZero(configData->sQnoise, configData->numStates, configData->numStates);
    mSetZero(configData->measNoise, configData->numObs, configData->numObs);
    
    
    /*! - Set lambda/eta to standard value for unscented kalman filters */
    configData->lambdaVal = configData->alpha*configData->alpha*
    (configData->numStates + configData->kappa) - configData->numStates;
    configData->eta = sqrt(configData->numStates + configData->lambdaVal);
    
    
    /*! - Set the wM/wC vectors to standard values for unscented kalman filters*/
    configData->wM[0] = configData->lambdaVal / (configData->numStates +
                                                 configData->lambdaVal);
    configData->wC[0] = configData->lambdaVal / (configData->numStates +
                                                 configData->lambdaVal) + (1 - configData->alpha*configData->alpha + configData->beta);
    for (i = 1; i<configData->countHalfSPs * 2 + 1; i++)
    {
        configData->wM[i] = 1.0 / 2.0*1.0 / (configData->numStates + configData->lambdaVal);
        configData->wC[i] = configData->wM[i];
    }
    
    vCopy(configData->stateInit, configData->numStates, configData->state);
    /*! - User a cholesky decomposition to obtain the sBar and sQnoise matrices for use in filter at runtime*/
    mCopy(configData->covarInit, configData->numStates, configData->numStates,
          configData->sBar);
    mCopy(configData->covarInit, configData->numStates, configData->numStates,
          configData->covar);
    
    mSetZero(tempMatrix, configData->numStates, configData->numStates);
    badUpdate += ukfCholDecomp(configData->sBar, configData->numStates,
                               configData->numStates, tempMatrix);
    
    badUpdate += ukfCholDecomp(configData->qNoise, configData->numStates,
                               configData->numStates, configData->sQnoise);
    
    mCopy(tempMatrix, configData->numStates, configData->numStates,
          configData->sBar);
    mTranspose(configData->sQnoise, configData->numStates,
               configData->numStates, configData->sQnoise);
    
    configData->timeTagOut = configData->timeTag;
    
    if (badUpdate <0){
        BSK_PRINT(MSG_WARNING, "Reset method contained bad update");
    }
    return;
}

/*! This method takes the relative position measurements and outputs an estimate of the
 spacecraft states in the intertial frame.
 @return void
 @param configData The configuration data associated with the OD filter
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Update_biasODuKF(BiasODuKFConfig *configData, uint64_t callTime,
                        uint64_t moduleId)
{
    double newTimeTag = 0.0;  /* [s] Local Time-tag variable*/
    uint64_t timeOfMsgWritten; /* [ns] Read time for the message*/
    uint32_t sizeOfMsgWritten = 0;  /* [-] Non-zero size indicates we received ST msg*/
    int32_t trackerValid; /* [-] Indicates whether the star tracker was valid*/
    double yBar[ODUKF_N_MEAS], tempYVec[ODUKF_N_MEAS];
    int i, computePostFits;
    BiasOpNavFilterMsg biasFilterOutBuffer; /* [-] Output filter info*/
    BiasOpNavMsg outputBiasOD;
    
    computePostFits = 0;
    v3SetZero(configData->postFits);
    memset(&outputBiasOD, 0x0, sizeof(BiasOpNavMsg));
    memset(&biasFilterOutBuffer, 0x0, sizeof(BiasOpNavFilterMsg));
    memset(&configData->cameraSpecs, 0x0, sizeof(CameraConfigMsg));
    memset(&configData->attInfo, 0x0, sizeof(NavAttIntMsg));
    memset(&configData->circlesIn, 0x0, sizeof(CirclesOpNavMsg));
    memset(&configData->pixelLineInMsg, 0x0, sizeof(OpNavFswMsg));
    
    /*! - read input messages */
    ReadMessage(configData->cameraConfigMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(CameraConfigMsg), &configData->cameraSpecs, moduleId);
    ReadMessage(configData->circlesInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(CirclesOpNavMsg), &configData->circlesIn, moduleId);
    ReadMessage(configData->attInMsgID, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(NavAttIntMsg), &configData->attInfo, moduleId);
    ReadMessage(configData->navInMsgId, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(NavTransIntMsg), &configData->filterInMsg, moduleId);
    ReadMessage(configData->opNavInMsgId, &timeOfMsgWritten, &sizeOfMsgWritten,
                sizeof(OpNavFswMsg), &configData->pixelLineInMsg, moduleId);
    
    m33SetIdentity((double (*)[3]) configData->measNoise);

    /*! - Handle initializing time in filter and discard initial messages*/
    trackerValid = 0;
    /*! - If the time tag from the measured data is new compared to previous step,
     propagate and update the filter*/
    newTimeTag = timeOfMsgWritten * NANO2SEC;
    if(newTimeTag >= configData->timeTag && sizeOfMsgWritten > 0 && configData->pixelLineInMsg.valid ==1)
    {
        configData->planetId = configData->pixelLineInMsg.planetID;
        biasODuKFTimeUpdate(configData, newTimeTag);
        biasODuKFMeasUpdate(configData);
        computePostFits = 1;
    }
    /*! - If current clock time is further ahead than the measured time, then
     propagate to this current time-step*/
    newTimeTag = callTime*NANO2SEC;
    if(newTimeTag >= configData->timeTag)
    {
        biasODuKFTimeUpdate(configData, newTimeTag);
    }
    
    /*! - The post fits are y - ybar if a measurement was read, if observations are zero, do not compute post fit residuals*/
    if(computePostFits == 1){
        /*! - Compute Post Fit Residuals, first get Y (eq 22) using the states post fit*/
        biasODuKFMeasModel(configData);

        /*! - Compute the value for the yBar parameter (equation 23)*/
        vSetZero(yBar, configData->numObs);
        for(i=0; i<configData->countHalfSPs*2+1; i++)
        {
            vCopy(&(configData->yMeas[i*configData->numObs]), configData->numObs,
                  tempYVec);
            vScale(configData->wM[i], tempYVec, configData->numObs, tempYVec);
            vAdd(yBar, configData->numObs, tempYVec, yBar);
        }
         mSubtract(configData->obs, ODUKF_N_MEAS, 1, yBar, configData->postFits);
    }
    
   
    /*! - Write the relative OD estimate into the copy of the navigation message structure*/
    v3Copy(configData->state, outputBiasOD.bias_pxl);
    outputBiasOD.timeTag = configData->timeTag;
    WriteMessage(configData->biasStateOutMsgId, callTime, sizeof(BiasOpNavMsg),
                 &(outputBiasOD), moduleId);
    
    /*! - Populate the filter states output buffer and write the output message*/
    biasFilterOutBuffer.timeTag = configData->timeTag;
    memmove(biasFilterOutBuffer.covar, configData->covar,
            configData->numStates*configData->numStates*sizeof(double));
    memmove(biasFilterOutBuffer.state, configData->state, configData->numStates*sizeof(double));
    memmove(biasFilterOutBuffer.postFitRes, configData->postFits, configData->imageObsNum*sizeof(double));
    WriteMessage(configData->biasFiltOutMsgId, callTime, sizeof(BiasOpNavFilterMsg),
                 &biasFilterOutBuffer, moduleId);
    
    return;
}


/*! This method performs the time update for the relative OD kalman filter.
 It propagates the sigma points forward in time and then gets the current
 covariance and state estimates.
 @return void
 @param configData The configuration data associated with the OD filter
 @param updateTime The time that we need to fix the filter to (seconds)
 */
int biasODuKFTimeUpdate(BiasODuKFConfig *configData, double updateTime)
{
    int i, Index;
    double sBarT[ODUKF_N_STATES_B*ODUKF_N_STATES_B]; // Sbar transpose (chol decomp of covar)
    double xComp[ODUKF_N_STATES_B], AT[(2 * ODUKF_N_STATES_B + ODUKF_N_STATES_B)*ODUKF_N_STATES_B]; // Intermediate state, process noise chol decomp
    double aRow[ODUKF_N_STATES_B], rAT[ODUKF_N_STATES_B*ODUKF_N_STATES_B], xErr[ODUKF_N_STATES_B]; //Row of A mat, R of QR decomp of A, state error
    double sBarUp[ODUKF_N_STATES_B*ODUKF_N_STATES_B]; // S bar cholupdate
    double *spPtr; //sigma point intermediate varaible
    double procNoise[ODUKF_N_STATES_B*ODUKF_N_STATES_B]; //process noise
    int32_t badUpdate=0;
    
    configData->dt = updateTime - configData->timeTag;
    vCopy(configData->state, configData->numStates, configData->statePrev);
    mCopy(configData->sBar, configData->numStates, configData->numStates, configData->sBarPrev);
    mCopy(configData->covar, configData->numStates, configData->numStates, configData->covarPrev);
    
    /*! - Read the planet ID from the message*/
    if(configData->planetIdInit == 0){BSK_PRINT(MSG_ERROR, "Need a planet to navigate")}
    
    mCopy(configData->sQnoise, configData->numStates, configData->numStates, procNoise);
    /*! - Copy over the current state estimate into the 0th Sigma point and propagate by dt*/
    vCopy(configData->state, configData->numStates,
          &(configData->SP[0 * configData->numStates + 0]));

    /*! - Scale that Sigma point by the appopriate scaling factor (Wm[0])*/
    vScale(configData->wM[0], &(configData->SP[0]),
           configData->numStates, configData->xBar);
    /*! - Get the transpose of the sBar matrix because it is easier to extract Rows vs columns*/
    mTranspose(configData->sBar, configData->numStates, configData->numStates,
               sBarT);
    /*! - For each Sigma point, apply sBar-based error, propagate forward, and scale by Wm just like 0th.
     Note that we perform +/- sigma points simultaneously in loop to save loop values.*/
    for (i = 0; i<configData->countHalfSPs; i++)
    {
        /*! - Adding covariance columns from sigma points*/
        Index = i + 1;
        spPtr = &(configData->SP[Index*configData->numStates]);
        vCopy(&sBarT[i*configData->numStates], configData->numStates, spPtr);
        vScale(configData->eta, spPtr, configData->numStates, spPtr);
        vAdd(spPtr, configData->numStates, configData->state, spPtr);
        vScale(configData->wM[Index], spPtr, configData->numStates, xComp);
        vAdd(xComp, configData->numStates, configData->xBar, configData->xBar);
        /*! - Subtracting covariance columns from sigma points*/
        Index = i + 1 + configData->countHalfSPs;
        spPtr = &(configData->SP[Index*configData->numStates]);
        vCopy(&sBarT[i*configData->numStates], configData->numStates, spPtr);
        vScale(-configData->eta, spPtr, configData->numStates, spPtr);
        vAdd(spPtr, configData->numStates, configData->state, spPtr);
        vScale(configData->wM[Index], spPtr, configData->numStates, xComp);
        vAdd(xComp, configData->numStates, configData->xBar, configData->xBar);
    }
    /*! - Zero the AT matrix prior to assembly*/
    mSetZero(AT, (2 * configData->countHalfSPs + configData->numStates),
             configData->countHalfSPs);
    /*! - Assemble the AT matrix.  Note that this matrix is the internals of
     the qr decomposition call in the source design documentation.  It is
     the inside of equation 20 in that document*/
    for (i = 0; i<2 * configData->countHalfSPs; i++)
    {
        vScale(-1.0, configData->xBar, configData->numStates, aRow);
        vAdd(aRow, configData->numStates,
             &(configData->SP[(i+1)*configData->numStates]), aRow);
        /*Check sign of wC to know if the sqrt will fail*/
        if (configData->wC[i+1]<=0){
            biasODuKFCleanUpdate(configData);
            return -1;}
        vScale(sqrt(configData->wC[i+1]), aRow, configData->numStates, aRow);
        memcpy((void *)&AT[i*configData->numStates], (void *)aRow,
               configData->numStates*sizeof(double));
        
    }
    /*! - Pop the sQNoise matrix on to the end of AT prior to getting QR decomposition*/
    memcpy(&AT[2 * configData->countHalfSPs*configData->numStates],
           procNoise, configData->numStates*configData->numStates
           *sizeof(double));
    /*! - QR decomposition (only R computed!) of the AT matrix provides the new sBar matrix*/
    ukfQRDJustR(AT, 2 * configData->countHalfSPs + configData->numStates,
                configData->countHalfSPs, rAT);
    
    mCopy(rAT, configData->numStates, configData->numStates, sBarT);
    mTranspose(sBarT, configData->numStates, configData->numStates,
               configData->sBar);
    
    /*! - Shift the sBar matrix over by the xBar vector using the appropriate weight
     like in equation 21 in design document.*/
    vScale(-1.0, configData->xBar, configData->numStates, xErr);
    vAdd(xErr, configData->numStates, &configData->SP[0], xErr);
    
    /*! - The bias covariance must be scaled toa  factor of gamma^{-1/2}, so the covariance is split and reconstructed.*/
//    badUpdate += ukfCholDownDate(configData->sBar, xErr, configData->wC[0],
//                                 configData->numStates, sBarUp);
    mScale(1./sqrt(configData->gamma), configData->sBar, ODUKF_N_MEAS, ODUKF_N_MEAS, sBarUp);
    /*! - Save current sBar matrix, covariance, and state estimate off for further use*/
    mCopy(sBarUp, configData->numStates, configData->numStates, configData->sBar);
    mTranspose(configData->sBar, configData->numStates, configData->numStates,
               configData->covar);
    mMultM(configData->sBar, configData->numStates, configData->numStates,
           configData->covar, configData->numStates, configData->numStates,
           configData->covar);
    vCopy(&(configData->SP[0]), configData->numStates, configData->state);
    
    if (badUpdate<0){
        biasODuKFCleanUpdate(configData);
        return(-1);}
    else{
        configData->timeTag = updateTime;
    }
    return(0);
}

/*! This method computes the measurement model.  Given that the data is coming from
 the pixelLine Converter, the transformation has already taken place from pixel data to spacecraft position.
 @return void
 @param configData The configuration data associated with the OD filter
 */
void biasODuKFMeasModel(BiasODuKFConfig *configData)
{
    int i, j;
    double dcm_CN[3][3], dcm_CB[3][3], dcm_BN[3][3];
    double reCentered[2], centers[2], radius, rNorm, denom, planetRad;
    double r_C[3];
    
    vSetZero(configData->obs, configData->numObs);
    
    rNorm = v3Norm(configData->filterInMsg.r_BN_N);
    planetRad = 0;

    MRP2C(configData->cameraSpecs.sigma_CB, dcm_CB);
    MRP2C(configData->attInfo.sigma_BN, dcm_BN);
    m33tMultM33(dcm_CB, dcm_BN, dcm_CN);
    
    m33MultV3(dcm_CN, configData->filterInMsg.r_BN_N, r_C);
    v3Scale(1./r_C[2], r_C, r_C);
    
    /*! - Find pixel size using camera specs */
    double X, Y;
    X = configData->cameraSpecs.sensorSize[0]*0.001/configData->cameraSpecs.resolution[0]; // mm to meters
    Y = configData->cameraSpecs.sensorSize[1]*0.001/configData->cameraSpecs.resolution[1];
    reCentered[0] = r_C[0]*configData->cameraSpecs.focalLength/X;
    reCentered[1] = r_C[1]*configData->cameraSpecs.focalLength/Y;
    
    centers[0] = reCentered[0] + configData->cameraSpecs.resolution[0]/2 - 0.5;
    centers[1] = reCentered[1] + configData->cameraSpecs.resolution[1]/2 - 0.5;

    if(configData->pixelLineInMsg.planetID > 0){
        if(configData->pixelLineInMsg.planetID ==1){
            planetRad = REQ_EARTH;//in km
        }
        if(configData->pixelLineInMsg.planetID ==2){
            planetRad = REQ_MARS;//in km
        }
        if(configData->pixelLineInMsg.planetID ==3){
            planetRad = REQ_JUPITER;//in km
        }
    }
    denom = planetRad/rNorm*1E3;
    radius = configData->cameraSpecs.focalLength/X*tan(asin(denom));
    
    for(j=0; j<configData->countHalfSPs*2+1; j++)
    {
        for(i=0; i<3; i++){
            configData->yMeas[i*(configData->countHalfSPs*2+1) + j] = configData->SP[i + j*configData->numStates];;
        }
    }
    
    v3Set(configData->circlesIn.circlesCenters[0] - centers[0], configData->circlesIn.circlesCenters[1] - centers[1], configData->circlesIn.circlesRadii[0]- radius,configData->obs);
    
    /*! - yMeas matrix was set backwards deliberately so we need to transpose it through*/
    mTranspose(configData->yMeas, configData->numObs, configData->countHalfSPs*2+1,
               configData->yMeas);
    
}

/*! This method performs the measurement update for the kalman filter.
 It applies the observations in the obs vectors to the current state estimate and
 updates the state/covariance with that information.
 @return void
 @param configData The configuration data associated with the OD filter */
int biasODuKFMeasUpdate(BiasODuKFConfig *configData)
{
    uint32_t i;
    int32_t badUpdate;
    double yBar[ODUKF_N_MEAS], syInv[ODUKF_N_MEAS*ODUKF_N_MEAS];
    double kMat[ODUKF_N_STATES_B*ODUKF_N_MEAS];
    double xHat[ODUKF_N_STATES_B], sBarT[ODUKF_N_STATES_B*ODUKF_N_STATES_B], tempYVec[ODUKF_N_MEAS];
    double AT[(2 * ODUKF_N_STATES_B + ODUKF_N_MEAS)*ODUKF_N_MEAS], qChol[ODUKF_N_MEAS*ODUKF_N_MEAS];
    double rAT[ODUKF_N_MEAS*ODUKF_N_MEAS], syT[ODUKF_N_MEAS*ODUKF_N_MEAS];
    double sy[ODUKF_N_MEAS*ODUKF_N_MEAS], Ucol[ODUKF_N_STATES_B];
    double updMat[ODUKF_N_MEAS*ODUKF_N_MEAS], pXY[ODUKF_N_STATES_B*ODUKF_N_MEAS], Umat[ODUKF_N_STATES_B*ODUKF_N_MEAS];
    badUpdate = 0;
    
    vCopy(configData->state, configData->numStates, configData->statePrev);
    mCopy(configData->sBar, configData->numStates, configData->numStates, configData->sBarPrev);
    mCopy(configData->covar, configData->numStates, configData->numStates, configData->covarPrev);
    
    /*! - Compute the valid observations and the measurement model for all observations*/
    biasODuKFMeasModel(configData);
    
    /*! - Compute the value for the yBar parameter (note that this is equation 23 in the
     time update section of the reference document*/
    vSetZero(yBar, configData->numObs);
    for(i=0; i<configData->countHalfSPs*2+1; i++)
    {
        vCopy(&(configData->yMeas[i*configData->numObs]), configData->numObs,
              tempYVec);
        vScale(configData->wM[i], tempYVec, configData->numObs, tempYVec);
        vAdd(yBar, configData->numObs, tempYVec, yBar);
    }
    
    /*! - Populate the matrix that we perform the QR decomposition on in the measurement
     update section of the code.  This is based on the differenence between the yBar
     parameter and the calculated measurement models.  Equation 24 in driving doc. */
    mSetZero(AT, configData->countHalfSPs*2+configData->numObs,
             configData->numObs);
    for(i=0; i<configData->countHalfSPs*2; i++)
    {
        vScale(-1.0, yBar, configData->numObs, tempYVec);
        vAdd(tempYVec, configData->numObs,
             &(configData->yMeas[(i+1)*configData->numObs]), tempYVec);
        if (configData->wC[i+1]<0){return -1;}
        vScale(sqrt(configData->wC[i+1]), tempYVec, configData->numObs, tempYVec);
        memcpy(&(AT[i*configData->numObs]), tempYVec,
               configData->numObs*sizeof(double));
    }
    
    /*! - This is the square-root of the Rk matrix which we treat as the Cholesky
     decomposition of the observation variance matrix constructed for our number
     of observations*/
    ukfCholDecomp(configData->measNoise, configData->numObs, configData->numObs, qChol);
    memcpy(&(AT[2*configData->countHalfSPs*configData->numObs]),
           qChol, configData->numObs*configData->numObs*sizeof(double));
    
    /*! - Perform QR decomposition (only R again) of the above matrix to obtain the
     current Sy matrix*/
    ukfQRDJustR(AT, 2*configData->countHalfSPs+configData->numObs,
                configData->numObs, rAT);
    mCopy(rAT, configData->numObs, configData->numObs, syT);
    mTranspose(syT, configData->numObs, configData->numObs, sy);
    /*! - Shift the matrix over by the difference between the 0th SP-based measurement
     model and the yBar matrix (cholesky down-date again)*/
    vScale(-1.0, yBar, configData->numObs, tempYVec);
    vAdd(tempYVec, configData->numObs, &(configData->yMeas[0]), tempYVec);
    badUpdate += ukfCholDownDate(sy, tempYVec, configData->wC[0],
                                 configData->numObs, updMat);
    /*! - Shifted matrix represents the Sy matrix */
    mCopy(updMat, configData->numObs, configData->numObs, sy);
    mTranspose(sy, configData->numObs, configData->numObs, syT);
    
    /*! - Construct the Pxy matrix (equation 26) which multiplies the Sigma-point cloud
     by the measurement model cloud (weighted) to get the total Pxy matrix*/
    mSetZero(pXY, configData->numStates, configData->numObs);
    for(i=0; i<2*configData->countHalfSPs+1; i++)
    {
        vScale(-1.0, yBar, configData->numObs, tempYVec);
        vAdd(tempYVec, configData->numObs,
             &(configData->yMeas[i*configData->numObs]), tempYVec);
        vSubtract(&(configData->SP[i*configData->numStates]), configData->numStates,
                  configData->xBar, xHat);
        vScale(configData->wC[i], xHat, configData->numStates, xHat);
        mMultM(xHat, configData->numStates, 1, tempYVec, 1, configData->numObs,
               kMat);
        mAdd(pXY, configData->numStates, configData->numObs, kMat, pXY);
    }
    
    /*! - Then we need to invert the SyT*Sy matrix to get the Kalman gain factor.  Since
     The Sy matrix is lower triangular, we can do a back-sub inversion instead of
     a full matrix inversion.  That is the ukfUInv and ukfLInv calls below.  Once that
     multiplication is done (equation 27), we have the Kalman Gain.*/
    badUpdate += ukfUInv(syT, configData->numObs, configData->numObs, syInv);
    
    mMultM(pXY, configData->numStates, configData->numObs, syInv,
           configData->numObs, configData->numObs, kMat);
    badUpdate += ukfLInv(sy, configData->numObs, configData->numObs, syInv);
    mMultM(kMat, configData->numStates, configData->numObs, syInv,
           configData->numObs, configData->numObs, kMat);
    
    
    /*! - Difference the yBar and the observations to get the observed error and
     multiply by the Kalman Gain to get the state update.  Add the state update
     to the state to get the updated state value (equation 27).*/
    vSubtract(configData->obs, configData->numObs, yBar, tempYVec);
    mMultM(kMat, configData->numStates, configData->numObs, tempYVec,
           configData->numObs, 1, xHat);
    vAdd(configData->state, configData->numStates, xHat, configData->state);
    /*! - Compute the updated matrix U from equation 28.  Note that I then transpose it
     so that I can extract "columns" from adjacent memory*/
    mMultM(kMat, configData->numStates, configData->numObs, sy,
           configData->numObs, configData->numObs, Umat);
    mTranspose(Umat, configData->numStates, configData->numObs, Umat);
    /*! - For each column in the update matrix, perform a cholesky down-date on it to
     get the total shifted S matrix (called sBar in internal parameters*/
    for(i=0; i<configData->numObs; i++)
    {
        vCopy(&(Umat[i*configData->numStates]), configData->numStates, Ucol);
        badUpdate += ukfCholDownDate(configData->sBar, Ucol, -1.0, configData->numStates, sBarT);
        mCopy(sBarT, configData->numStates, configData->numStates,
              configData->sBar);
    }
    /*! - Compute equivalent covariance based on updated sBar matrix*/
    mTranspose(configData->sBar, configData->numStates, configData->numStates,
               configData->covar);
    mMultM(configData->sBar, configData->numStates, configData->numStates,
           configData->covar, configData->numStates, configData->numStates,
           configData->covar);
    
    if (badUpdate<0){
        biasODuKFCleanUpdate(configData);
        return(-1);}
    return(0);
}

/*! This method cleans the filter states after a bad upadate on the fly.
 It removes the potentially corrupted previous estimates and puts the filter
 back to a working state.
 @return void
 @param configData The configuration data associated with the OD filter
 */
void biasODuKFCleanUpdate(BiasODuKFConfig *configData){
    int i;
    /*! - Reset the observations, state, and covariannces to a previous safe value*/
    vSetZero(configData->obs, configData->numObs);
    vCopy(configData->statePrev, configData->numStates, configData->state);
    mCopy(configData->sBarPrev, configData->numStates, configData->numStates, configData->sBar);
    mCopy(configData->covarPrev, configData->numStates, configData->numStates, configData->covar);
    
    /*! - Reset the wM/wC vectors to standard values for unscented kalman filters*/
    configData->wM[0] = configData->lambdaVal / (configData->numStates +
                                                 configData->lambdaVal);
    configData->wC[0] = configData->lambdaVal / (configData->numStates +
                                                 configData->lambdaVal) + (1 - configData->alpha*configData->alpha + configData->beta);
    for (i = 1; i<configData->countHalfSPs * 2 + 1; i++)
    {
        configData->wM[i] = 1.0 / 2.0*1.0 / (configData->numStates +
                                             configData->lambdaVal);
        configData->wC[i] = configData->wM[i];
    }
    
    return;
}

