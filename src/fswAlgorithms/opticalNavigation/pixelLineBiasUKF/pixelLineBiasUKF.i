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
%module pixelLineBiasUKF
%{
   #include "pixelLineBiasUKF.h"
   #include "../_GeneralModuleFiles/ukfUtilities.h"
%}

%include "swig_conly_data.i"
%constant void Update_pixelLineBiasUKF(void*, uint64_t, uint64_t);
%ignore Update_pixelLineBiasUKF;
%constant void SelfInit_pixelLineBiasUKF(void*, uint64_t);
%ignore SelfInit_pixelLineBiasUKF;
%constant void CrossInit_pixelLineBiasUKF(void*, uint64_t);
%ignore CrossInit_pixelLineBiasUKF;
%constant void Reset_pixelLineBiasUKF(void*, uint64_t, uint64_t);
%ignore Reset_pixelLineBiasUKF;

%include "pixelLineBiasUKF.h"
%include "../_GeneralModuleFiles/ukfUtilities.h"

%include "cMsgPayloadDef/CameraConfigMsgPayload.h"
struct CameraConfigMsg_C;
%include "cMsgPayloadDef/NavAttMsgPayload.h"
struct NavAttMsg_C;
%include "cMsgPayloadDef/PixelLineFilterMsgPayload.h"
struct PixelLineFilterMsg_C;
%include "cMsgPayloadDef/NavTransMsgPayload.h"
struct NavTransMsg_C;
%include "cMsgPayloadDef/CirclesOpNavMsgPayload.h"
struct CirclesOpNavMsg_C;

%pythoncode %{
import sys
protectAllClasses(sys.modules[__name__])
%}

