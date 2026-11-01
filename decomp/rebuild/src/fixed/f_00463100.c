/* 0x00463100: (float)F(0x1c4)->[0x1c8] (unsigned) * F(0x24), rounded to float */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0068AE08[];

DECOMP(00463100)
float __thiscall f_00463100(int this_ptr)
{
    int *p = *(int **)(this_ptr + 0x1c4);
    float v = (float)p[0x1c8 / 4];

    if (p[0x1c8 / 4] < 0)
        v = v + *(float *)d_0068AE08;
    {
        volatile float r = v * *(float *)(this_ptr + 0x24);

        return r;
    }
}
