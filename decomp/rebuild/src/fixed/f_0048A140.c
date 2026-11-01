/* 0x0048A140: multiplies the three floats at *this by 1/param; the reciprocal is rounded to float first
 * (fld1; fdivrp; fstp dword [esp+4]), which the generated code kept in extended precision. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0048A140)
void __thiscall f_0048A140(void *this, float param_1)
{
    volatile float inv = 1.0 / param_1;

    *(float *)this = *(float *)this * inv;
    *(float *)((char *)this + 4) = *(float *)((char *)this + 4) * inv;
    *(float *)((char *)this + 8) = inv * *(float *)((char *)this + 8);
}
