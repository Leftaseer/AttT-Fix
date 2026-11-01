/* 0x0047CE60: F(0xa4) = 1, F(0x84) = F(0x88) = i, F(0x94) = F(0x9c) / f, F(0x98) = 1 / f, where f is the int as
 * a float (a negative one biased by 2^32, the unsigned conversion).  The original computes the sum in extended
 * precision and rounds it to float once (fild; fadd dword [0x68ae08]; fstp dword [esp+4]) before the two
 * divisions; clang keeps a float local unrounded on the x87 stack, so the quotient came out 1 ulp off. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_0068AE08[];

DECOMP(0047CE60)
void __thiscall f_0047CE60(void *this, int param_1)
{
    double t = (double)param_1;

    *(unsigned char *)((int)this + 0xa4) = 1;
    *(int *)((int)this + 0x84) = param_1;
    *(int *)((int)this + 0x88) = param_1;
    if (param_1 < 0)
        t = t + (double)*(float *)d_0068AE08;
    {
        volatile float f = (float)t;

        *(float *)((int)this + 0x94) = *(float *)((int)this + 0x9c) / f;
        *(float *)((int)this + 0x98) = 1.0 / f;
    }
}
