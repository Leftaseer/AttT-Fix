/* 0x0042D850: resets the 16-float block at arg 1: its four corners (0, 5, 10, 15) take the distance 0x0068AE40,
 * every other float 0. */
#include "auto_pre.h"
DECOMP_C char d_0068AE40[];

DECOMP(0042D850)
void __cdecl f_0042D850(void *self)
{
    float *f = (float *)self;
    float d = *(float *)d_0068AE40;

    f[0] = f[5] = f[10] = f[15] = d;
    f[1] = f[2] = f[3] = f[4] = f[6] = f[7] = f[8] = f[9] = 0.0f;
    f[11] = f[12] = f[13] = f[14] = 0.0f;
}
