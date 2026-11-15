/* 0x00426810: the virtual at +0x80 gets x negated and scaled by the double at 0x00607CE0 (0.5), then the one at
 * +0xac gets the original x.  The vtable is reloaded for the second call. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[];

DECOMP(00426810)
unsigned int __thiscall f_00426810(void *self, float x)
{
    float sx = (float)(-(double)x * *(double *)d_00607CE0);
    (*(void (__thiscall **)(void *, float))(*(char **)self + 0x80))(self, sx);
    return (*(unsigned int (__thiscall **)(void *, float))(*(char **)self + 0xac))(self, x);
}
