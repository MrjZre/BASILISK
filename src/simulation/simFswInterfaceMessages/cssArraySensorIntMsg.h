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

#ifndef CSS_ARRAY_SENSOR_MESSAGE_H
#define CSS_ARRAY_SENSOR_MESSAGE_H

#include "macroDefinitions.h"

/*! @brief Output structure for CSS array or constellation interface.  Each element contains the raw measurement which should be a cosine value nominally */
typedef struct {
    double CosValue[MAX_NUM_CSS_SENSORS];   /*!< Current measured CSS value (ideally a cosine value) 
                                                 for the constellation of CSS sensors*/
}CSSArraySensorIntMsg;

#endif
