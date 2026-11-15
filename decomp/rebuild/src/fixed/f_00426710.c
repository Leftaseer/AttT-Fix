/* 0x00426710: the virtual at +0x84 gets the y offset from the size (+0x78) scaled by the double at 0x00608090
 * (-0.5), then the one at +0xa0 gets the original y.  The vtable is reloaded for the second call. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608090[];

DECOMP(00426710)
unsigned int __thiscall f_00426710(void *self, float y)
{
    char *s = (char *)self;
    float sy = (float)(((double)y - (double)*(float *)(s + 0x78)) * *(double *)d_00608090);
    (*(void (__thiscall **)(void *, float))(*(char **)self + 0x84))(self, sy);
    return (*(unsigned int (__thiscall **)(void *, float))(*(char **)self + 0xa0))(self, y);
}
