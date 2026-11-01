/* 0x004631F0: (float)F(0x1dc)->[0x1cc] / (float)F(0x1dc)->[0x1c4]->[0x1c8] (unsigned), rounded to float */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0068AE08[];

DECOMP(004631F0)
float __thiscall f_004631F0(int this_ptr)
{
    char *p = *(char **)(this_ptr + 0x1dc);
    int *q = *(int **)(p + 0x1c4);
    float a = (float)*(int *)(p + 0x1cc);
    float b = (float)q[0x1c8 / 4];

    if (*(int *)(p + 0x1cc) < 0)
        a = a + *(float *)d_0068AE08;
    if (q[0x1c8 / 4] < 0)
        b = b + *(float *)d_0068AE08;
    {
        volatile float r = a / b;

        return r;
    }
}
