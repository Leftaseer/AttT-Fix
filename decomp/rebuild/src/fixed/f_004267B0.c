/* 0x004267B0: the virtual at +0x78 gets the point (x, y) negated and scaled by the double at 0x00607CE0 (0.5),
 * then the one at +0xa4 gets the original point.  The vtable is reloaded for the second call. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[];

DECOMP(004267B0)
unsigned int __thiscall f_004267B0(void *self, float x, float y)
{
    double k = *(double *)d_00607CE0;
    float sx = (float)(-(double)x * k);
    float sy = (float)(-(double)y * k);
    (*(void (__thiscall **)(void *, float, float))(*(char **)self + 0x78))(self, sx, sy);
    return (*(unsigned int (__thiscall **)(void *, float, float))(*(char **)self + 0xa4))(self, x, y);
}
