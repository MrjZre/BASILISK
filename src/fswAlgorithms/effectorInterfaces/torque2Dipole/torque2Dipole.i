/*
 ISC License

 Copyright (c) 2021, Autonomous Vehicle Systems Lab, University of Colorado Boulder

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

%module torque2Dipole
%{
    #include "torque2Dipole.h"
%}

%pythoncode %{
    from Basilisk.architecture.swig_common_model import *
%}
%include "swig_conly_data.i"
%constant void Update_torque2Dipole(void*, uint64_t, uint64_t);
%ignore Update_torque2Dipole;
%constant void SelfInit_torque2Dipole(void*, uint64_t);
%ignore SelfInit_torque2Dipole;
%constant void Reset_torque2Dipole(void*, uint64_t, uint64_t);
%ignore Reset_torque2Dipole;
%include "architecture/msgPayloadDefC/TAMSensorBodyMsgPayload.h"
struct TAMSensorBodyMsg_C;
%include "architecture/msgPayloadDefC/DipoleRequestBodyMsgPayload.h"
struct DipoleRequestBodyMsg_C;
%include "architecture/msgPayloadDefC/CmdTorqueBodyMsgPayload.h"
struct CmdTorqueBodyMsg_C;

%include "torque2Dipole.h"


%pythoncode %{
import sys
protectAllClasses(sys.modules[__name__])
%}

