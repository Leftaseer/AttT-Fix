/* 0x0045B7C0: squared distance between F(0x298,0x29c,0x2a0) and F(0x244,0x248,0x24c): the differences are
 * rounded to float as the original stores them, then (a*a + b*b) + c*c, rounded to float */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0045B7C0)
float __thiscall f_0045B7C0(int this_ptr)
{
    volatile float a = *(float *)(this_ptr + 0x298) - *(float *)(this_ptr + 0x244);
    volatile float b = *(float *)(this_ptr + 0x29c) - *(float *)(this_ptr + 0x248);
    volatile float c = *(float *)(this_ptr + 0x2a0) - *(float *)(this_ptr + 0x24c);
    volatile float r = (a * a + b * b) + c * c;

    return r;
}
