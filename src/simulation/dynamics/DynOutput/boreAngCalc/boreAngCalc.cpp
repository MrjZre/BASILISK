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

#include "simulation/dynamics/DynOutput/boreAngCalc/boreAngCalc.h"
#include "architecture/utilities/linearAlgebra.h"
#include "architecture/utilities/rigidBodyKinematics.h"
#include "Eigen/Dense"
#include <math.h>
#include <cstring>
#include <iostream>

//! The constructor.  Note that you have to overwrite the message names.
BoreAngCalc::BoreAngCalc()
{
    CallCounts = 0;
    boreVecPoint[0] = boreVecPoint[1] = boreVecPoint[2]  = 0.0;
    this->localPlanet = this->celBodyInMsg.zeroMsgPayload;
    this->localState = this->scStateInMsg.zeroMsgPayload;
    return;
}

//! The destructor.  So tired of typing this.
BoreAngCalc::~BoreAngCalc()
{
    return;
}


/*! This method is used to reset the module.
 @return void
 */
void BoreAngCalc::Reset(uint64_t CurrentSimNanos)
{
    // check if required input messages have not been included
    if (!this->scStateInMsg.isLinked()) {
        bskLogger.bskLog(BSK_ERROR, "boreAngCalc.scStateInMsg was not linked.");
    }
    if (!this->celBodyInMsg.isLinked()) {
        bskLogger.bskLog(BSK_ERROR, "boreAngCalc.celBodyInMsg was not linked.");
    }

}

/*! This method writes the output data out into the messaging system.
 @return void
 @param CurrentClock The current time in the system for output stamping
 */
void BoreAngCalc::WriteOutputMessages(uint64_t CurrentClock)
{
    this->angOutMsg.write(&this->boresightAng, this->moduleID, CurrentClock);
}

/*! This method reads the input messages in from the system and sets the
 appropriate parameters
 @return void
 */
void BoreAngCalc::ReadInputs()
{
    //! - Read the input message into the correct pointer
    this->localState = this->scStateInMsg();
    this->localPlanet = this->celBodyInMsg();

    this->inputsGood = this->scStateInMsg.isWritten();
    this->inputsGood &= this->celBodyInMsg.isWritten();
}

/*! This method computes the vector specified in the input file in the LVLH 
    reference frame of the spacecraft above the target celestial body.  This 
    is used later to compute how far off that vector is in an angular sense.
    @return void
*/
void BoreAngCalc::computeAxisPoint()
{
    double dcm_BN[3][3];                /*!< dcm, inertial to body frame */
    double dcm_PoN[3][3];               /*!< dcm, inertial to Point frame */
    double dcm_BPo[3][3];               /*!< dcm, Point to body frame */
    double relPosVector[3];
    double relVelVector[3];
    double secPointVector[3];
    double primPointVector[3];
    
    MRP2C(localState.sigma_BN, dcm_BN);
    v3Subtract(localPlanet.PositionVector, localState.r_BN_N, relPosVector);
    v3Subtract(localPlanet.VelocityVector, localState.v_BN_N, relVelVector);
    v3Cross(relPosVector, relVelVector, secPointVector);
    v3Normalize(secPointVector, secPointVector);
    v3Normalize(relPosVector, primPointVector);
    v3Copy(primPointVector, &(dcm_PoN[0][0]));
    v3Cross(primPointVector, secPointVector, &(dcm_PoN[2][0]));
    v3Normalize(&(dcm_PoN[2][0]), &(dcm_PoN[2][0]));
    v3Cross(&(dcm_PoN[2][0]), &(dcm_PoN[0][0]),
            &(dcm_PoN[1][0]));
    m33MultM33t(dcm_BN, dcm_PoN, dcm_BPo);
    Eigen::MatrixXd vecBore_B = Eigen::Map<Eigen::MatrixXd>(boreVec_B, 3, 1);
    m33tMultV3(dcm_BPo, vecBore_B.data(), boreVecPoint);
    
}
/*! This method computes the output structure for messaging. The miss angle is 
    absolute distance between the desired body point and the specified structural 
    vector.  The aximuth angle is the angle between the y pointing axis and the 
    desired pointing vector projected into the y/z plane.
    @return void
*/
void BoreAngCalc::computeOutputData()
{
    // Define epsilon that will avoid atan2 giving a NaN.
    double eps = 1e-10;
    double baselinePoint[3] = {1.0, 0.0, 0.0};
    double dotValue = v3Dot(this->boreVecPoint, baselinePoint);
    this->boresightAng.missAngle = fabs(acos(dotValue));
    if(fabs(this->boreVecPoint[1]) < eps){
        this->boresightAng.azimuth = 0.0;
    }
    else {
        this->boresightAng.azimuth = atan2(this->boreVecPoint[2], this->boreVecPoint[1]);
    }
}

/*! This method is the main carrier for the boresight calculation routine.  If it detects
 that it needs to re-init (direction change maybe) it will re-init itself.
 Then it will compute the angles away that the boresight is from the celestial target.
 @return void
 @param CurrentSimNanos The current simulation time for system
 */
void BoreAngCalc::UpdateState(uint64_t CurrentSimNanos)
{
    //! - Read the input message and convert it over appropriately depending on switch
    ReadInputs();
   
    if(inputsGood)
    { 
        computeAxisPoint();
        computeOutputData();
    }
    
    //! Write out the current output for current time
    WriteOutputMessages(CurrentSimNanos);
}
