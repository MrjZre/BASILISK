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

%module simMessages
%{
#include <Eigen/Dense>
#include <vector>
#include "boreAngleSimMsg.h"
#include "cssRawDataSimMsg.h"
#include "spicePlanetStateSimMsg.h"
#include "thrOperationSimMsg.h"
#include "thrTimePairSimMsg.h"
#include "idEphemerisSimMsg.h"
#include "rwCmdSimMsg.h"
#include "rwConfigSimMsg.h"
#include "rwConfigLogSimMsg.h"
#include "scPlusMassPropsSimMsg.h"
#include "scPlusStatesSimMsg.h"
#include "spiceTimeSimMsg.h"
#include "syncClockSimMsg.h"
#include "thrConfigSimMsg.h"
#include "thrOutputSimMsg.h"
%}

%include "swig_conly_data.i"
%include "swig_common_model.i"

namespace std {
    %template(ThrusterTimeVector) vector<THRTimePairSimMsg>;
    %template(ThrusterConfigVector) vector<THRConfigSimMsg>;
}

%include "boreAngleSimMsg.h"
GEN_SIZEOF(AngOffValuesSimMsg)
%include "cssRawDataSimMsg.h"
GEN_SIZEOF(CSSRawDataSimMsg)
%include "idEphemerisSimMsg.h"
GEN_SIZEOF(IDEphemerisSimMsg)
%include "rwCmdSimMsg.h"
GEN_SIZEOF(RWCmdSimMsg)
%include "rwConfigSimMsg.h"
GEN_SIZEOF(RWConfigSimMsg);
%include "rwConfigLogSimMsg.h"
GEN_SIZEOF(RWConfigLogSimMsg);
%include "scPlusMassPropsSimMsg.h"
GEN_SIZEOF(SCPlusMassPropsSimMsg)
%include "scPlusStatesSimMsg.h"
GEN_SIZEOF(SCPlusStatesSimMsg)
%include "spicePlanetStateSimMsg.h"
GEN_SIZEOF(SpicePlanetStateSimMsg)
%include "spiceTimeSimMsg.h"
GEN_SIZEOF(SpiceTimeSimMsg)
%include "syncClockSimMsg.h"
GEN_SIZEOF(SynchClockSimMsg)
%include "thrConfigSimMsg.h"
GEN_SIZEOF(THRConfigSimMsg)
%include "thrOperationSimMsg.h"
GEN_SIZEOF(THROperationSimMsg)
%include "thrOutputSimMsg.h"
GEN_SIZEOF(THROutputSimMsg)
%include "thrTimePairSimMsg.h"
GEN_SIZEOF(THRTimePairSimMsg)

%pythoncode %{
    import sys
    protectAllClasses(sys.modules[__name__])
    %}
