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

#ifndef accessSimMsg_h
#define accessSimMsg_h

/*! \defgroup simMessages
 *  @{
 */

/*! @brief Message that defines access to spacecraft from a groundLocation, providing access, range, and elevation with
 * repect to a ground location.
 */
typedef struct {
    uint64_t hasAccess;//! [-] 1 when the writer has access to a spacecraft; 0 otherwise.
    double slantRange;//![m] Range from a location to the spacecraft.
    double elevation;//![deg] Elevation angle for a given spacecraft.
}AccessSimMsg;

/* @} */

#endif /* accessSimMsg.h */
