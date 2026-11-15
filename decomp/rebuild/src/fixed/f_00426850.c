/* 0x00426850: the virtual at +0x84 gets y negated and scaled by the double at 0x00607CE0 (0.5), then the one at
 * +0xb0 gets the original y.  The vtable is reloaded for the second call. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[];

DECOMP(00426850)
unsigned int __thiscall f_00426850(void *self, float y)
{
    float sy = (float)(-(double)y * *(double *)d_00607CE0);
    (*(void (__thiscall **)(void *, float))(*(char **)self + 0x84))(self, sy);
    return (*(unsigned int (__thiscall **)(void *, float))(*(char **)self + 0xb0))(self, y);
}
