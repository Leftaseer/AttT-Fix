#include "auto_pre.h"

DECOMP_C double __thiscall sub_0042AD00(void *track, int index);

/* @func 005201B0 */
DECOMP(005201B0)
void __thiscall f_005201B0(char *object, float *out, int index, unsigned int unused, float gain)
{
    (void)unused;
    void *track = *(void **)(object + 0x6c);
    // The original stores this product once as a float before scaling either axis.
    float delta = GH_FROUND(sub_0042AD00(track, index) * gain);
    out[0] = delta * *(float *)(object + 0x70);
    out[1] = delta * *(float *)(object + 0x74);
}
