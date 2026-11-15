/* 0x00426660: the virtual at +0x78 gets the offset of the point (x, y) from the size (+0x74/+0x78) scaled by the
 * double at 0x00608090 (-0.5), then the one at +0x94 gets the original point.  The vtable is reloaded for the second
 * call. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_00608090[];

DECOMP(00426660)
unsigned int __thiscall f_00426660(void *self, float x, float y)
{
    char *s = (char *)self;
    double k = *(double *)d_00608090;
    float sx = (float)(((double)x - (double)*(float *)(s + 0x74)) * k);
    float sy = (float)(((double)y - (double)*(float *)(s + 0x78)) * k);
    (*(void (__thiscall **)(void *, float, float))(*(char **)self + 0x78))(self, sx, sy);
    return (*(unsigned int (__thiscall **)(void *, float, float))(*(char **)self + 0x94))(self, x, y);
}
