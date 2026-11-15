/* 0x004266D0: the virtual at +0x80 gets the x offset from the size (+0x74) scaled by the double at 0x00608090
 * (-0.5), then the one at +0x9c gets the original x.  The vtable is reloaded for the second call. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608090[];

DECOMP(004266D0)
unsigned int __thiscall f_004266D0(void *self, float x)
{
    char *s = (char *)self;
    float sx = (float)(((double)x - (double)*(float *)(s + 0x74)) * *(double *)d_00608090);
    (*(void (__thiscall **)(void *, float))(*(char **)self + 0x80))(self, sx);
    return (*(unsigned int (__thiscall **)(void *, float))(*(char **)self + 0x9c))(self, x);
}
