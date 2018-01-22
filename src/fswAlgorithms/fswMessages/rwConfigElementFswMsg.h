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

#ifndef _RW_CONFIG_ELEMENT_MESSAGE_H
#define _RW_CONFIG_ELEMENT_MESSAGE_H


/*! @brief Structure used to define a single FSW RW configuration with vector in Structure S frame */
typedef struct {
    double gsHat_B[3];          /*!< [-] Spin axis unit vector of the wheel in structure */
    double Js;                  /*!< [kgm2] Spin axis inertia of the wheel */
    double uMax;                /*!< [Nm]   maximum RW motor torque */
}RWConfigElementFswMsg;



#endif
