
#ifndef ORB_ELEM_CONVERT_H
#define ORB_ELEM_CONVERT_H

#include <vector>
#include "utilities/sys_model.h"
#include "utilities/orbitalMotion.h"

/*! \addtogroup SimModelGroup
 * @{
 */

//! An orbital element/cartesian position and velocity converter
class OrbElemConvert: public SysModel {
public:
    OrbElemConvert();
    ~OrbElemConvert();
    
    void SelfInit();
    void CrossInit();
    void UpdateState(uint64_t CurrentSimNanos);
    void WriteOutputMessages(uint64_t CurrentClock);
    void Elements2Cartesian();
    void Cartesian2Elements();
    void ReadInputs();
    
public:
    double r_N[3];                    //!< m  Current position vector (inertial)
    double v_N[3];                    //!< m/s Current velocity vector (inertial)
    double mu;                        //!< -- Current grav param (inertial)
    classicElements CurrentElem;      //!< -- Current orbital elements
    std::string StateString;          //!< -- port to use for conversion
    std::string OutputDataString;     //!< -- port to use for output data
    uint64_t OutputBufferCount;       //!< -- Count on number of buffers to output
	uint64_t stateMsgSize;            //!< -- Size of the state message to use
    bool ReinitSelf;                  //!< -- Indicator to reset conversion type
    bool Elements2Cart;               //!< -- Flag saying which direction to go
	bool useEphemFormat;              //!< -- Flag indicating whether to use state or ephem
    bool inputsGood;                  //!< -- flag indicating that inputs are good
    
private:
    int64_t StateInMsgID;              // -- MEssage ID for incoming data
    int64_t StateOutMsgID;             // -- Message ID for outgoing data
};

/*! @} */

#endif
