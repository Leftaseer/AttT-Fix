/* 0x0042B7F0: the CArmyScreenScene constructor: the CScene base (0x004B20D0(0)), vtable 0x00608848 at +0x74,
 * the member slots +0x84..+0xAC and +0xB8..+0xCC zeroed, the scene's three vtables (0x0060888C at +0, 0x0060886C at
 * +4, 0x00608864 at +0x74), the +/- extents at +0xB0/+0xB4 (the screen size globals minus 800/600, halved) and the
 * zero byte at +0x158. Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B20D0(void *self, int a);
DECOMP_C char d_00608848[], d_00608864[], d_0060886C[], d_0060888C[];
DECOMP_C char d_006C8958[], d_006C895C[];                               /* float screen origin */
DECOMP_C char d_00607CE0[], d_00608850[], d_00608858[];                 /* double 0.5, 600, 800 */

DECOMP(0042B7F0)
void *__thiscall f_0042B7F0(char *this)
{
    unsigned int o;

    sub_004B20D0(this, 0);
    *(void **)(this + 0x74) = d_00608848;
    for (o = 0x84; o <= 0xac; o += 4)
        *(unsigned int *)(this + o) = 0;
    for (o = 0xb8; o <= 0xcc; o += 4)
        *(unsigned int *)(this + o) = 0;
    *(void **)this = d_0060888C;
    *(void **)(this + 4) = d_0060886C;
    *(void **)(this + 0x74) = d_00608864;
    *(float *)(this + 0xb0) = (float)((*(float *)d_006C895C - *(double *)d_00608858) * *(double *)d_00607CE0);
    *(float *)(this + 0xb4) = (float)((*(float *)d_006C8958 - *(double *)d_00608850) * *(double *)d_00607CE0);
    *(unsigned char *)(this + 0x158) = 0;
    return this;
}
