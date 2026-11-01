/* 0x0042D9A0: (int)((float)(f274 / f270) / f24): the first quotient is stored as a float (fstp dword) before
 * the second division, which the decompiler's one-expression form computes in extended precision */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042D9A0)
undefined4 __thiscall f_0042D9A0(int this_ptr)
{
    volatile float q = *(float *)(this_ptr + 0x274) / *(float *)(this_ptr + 0x270);

    return (undefined4)TRUNC(q / *(float *)(this_ptr + 0x24));
}
