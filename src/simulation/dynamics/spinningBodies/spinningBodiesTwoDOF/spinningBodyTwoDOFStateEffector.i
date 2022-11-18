/*
 ISC License

 Copyright (c) 2022, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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


%module spinningBodyTwoDOFStateEffector
%{
   #include "spinningBodyTwoDOFStateEffector.h"
%}

%pythoncode %{
from Basilisk.architecture.swig_common_model import *
%}

%include "std_string.i"
%include "std_vector.i"
%include "swig_conly_data.i"
%include "swig_eigen.i"

%include "sys_model.h"
%include "simulation/dynamics/_GeneralModuleFiles/stateData.h"
%include "simulation/dynamics/_GeneralModuleFiles/stateEffector.h"
%include "simulation/dynamics/_GeneralModuleFiles/dynParamManager.h"
%include "spinningBodyTwoDOFStateEffector.h"

%include "architecture/msgPayloadDefC/SCStatesMsgPayload.h"
struct SCStatesMsg_C;
%include "architecture/msgPayloadDefC/ArrayMotorTorqueMsgPayload.h"
struct ArrayMotorTorqueMsg_C;
%include "architecture/msgPayloadDefC/SpinningBodyMsgPayload.h"
struct SpinningBodyMsg_C;

%template(spinningBodyOutMsgs) std::vector<Message<SpinningBodyMsgPayload>*>;

%pythoncode %{
import sys
protectAllClasses(sys.modules[__name__])
%}
