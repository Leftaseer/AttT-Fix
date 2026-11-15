/* 0x0042AD00: the height change of key `index` (its z at +8 minus the previous key's z), 0 for the first key.
 * Returned through st0 as a double, so the float result is rounded first. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042AD00)
double __thiscall f_0042AD00(void *this, int index)
{
    const float *keys = *(const float **)((char *)this + 0x1d8);

    if (index == *(int *)((char *)this + 0x1d0))
        return 0.0;
    return GH_FROUND(keys[index * 3 + 2] - keys[index * 3 - 1]);
}
