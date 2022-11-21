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
%module prescribed1DOF
%{
   #include "prescribed1DOF.h"
%}

%include "swig_conly_data.i"
%constant void SelfInit_prescribed1DOF(void*, uint64_t);
%ignore SelfInit_prescribed1DOF;
%constant void Reset_prescribed1DOF(void*, uint64_t, uint64_t);
%ignore Reset_prescribed1DOF;
%constant void Update_prescribed1DOF(void*, uint64_t, uint64_t);
%ignore Update_prescribed1DOF;

%include "prescribed1DOF.h"

%include "architecture/msgPayloadDefC/RefAngleMsgPayload.h"
struct RefAngleMsg_C;
%include "architecture/msgPayloadDefC/prescribedMotionMsgPayload.h"
struct PrescribedMotionMsg_C;

%pythoncode %{
import sys
protectAllClasses(sys.modules[__name__])
%}
