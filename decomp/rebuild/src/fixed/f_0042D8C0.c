/* 0x0042D8C0: F(0x20) / F(0x1c), rounded to float (the original stores and reloads it) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042D8C0)
float __thiscall f_0042D8C0(int this_ptr)
{
    volatile float r = *(float *)(this_ptr + 0x20) / *(float *)(this_ptr + 0x1c);

    return r;
}
