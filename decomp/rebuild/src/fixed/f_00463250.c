/* 0x00463250: (float)F(0x1dc)->[0x1c4]->[0x1c8] (unsigned) * F(0x1dc)->[0x24], rounded to float */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0068AE08[];

DECOMP(00463250)
float __thiscall f_00463250(int this_ptr)
{
    char *p = *(char **)(this_ptr + 0x1dc);
    int *q = *(int **)(p + 0x1c4);
    float v = (float)q[0x1c8 / 4];

    if (q[0x1c8 / 4] < 0)
        v = v + *(float *)d_0068AE08;
    {
        volatile float r = v * *(float *)(p + 0x24);

        return r;
    }
}
