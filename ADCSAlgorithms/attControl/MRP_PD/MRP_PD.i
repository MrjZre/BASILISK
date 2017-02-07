/*
 ISC License

 Copyright (c) 2016-2017, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

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
%module MRP_PD
%{
   #include "MRP_PD.h"
%}

%include "swig_conly_data.i"
%constant void Update_MRP_PD(void*, uint64_t, uint64_t);
%ignore Update_MRP_PD;
%constant void SelfInit_MRP_PD(void*, uint64_t);
%ignore SelfInit_MRP_PD;
%constant void CrossInit_MRP_PD(void*, uint64_t);
%ignore CrossInit_MRP_PD;
%constant void Reset_MRP_PD(void*, uint64_t, uint64_t);
%ignore Reset_MRP_PD;
%include "../_GeneralModuleFiles/vehControlOut.h"
%include "../../fswMessages/attGuidMessage.h"
%include "../../fswMessages/vehicleConfigMessage.h"
GEN_SIZEOF(MRP_PDConfig);
GEN_SIZEOF(AttGuidMessage);
GEN_SIZEOF(VehicleConfigMessage);
%include "MRP_PD.h"
%pythoncode %{
import sys
protectAllClasses(sys.modules[__name__])
%}
