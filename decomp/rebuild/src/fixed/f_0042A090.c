/* 0x0042A090: the distance between two floats, |a - b| (the larger minus the smaller; a NaN leaves the original's
 * x87 stack empty, here a NaN) */
/* @conv - 8 */
#include "auto_pre.h"

DECOMP(0042A090)
float __stdcall f_0042A090(float a, float b)
{
    return b > a ? b - a : a - b;
}
