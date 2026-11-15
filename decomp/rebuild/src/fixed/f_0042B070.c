/* 0x0042B070: the height difference between two keys (key `a`'s z minus key `b`'s z) as a float. */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(0042B070)
float __thiscall f_0042B070(void *this, int a, int b)
{
    const float *keys = *(const float **)((char *)this + 0x1d8);
    return keys[a * 3 + 2] - keys[b * 3 + 2];
}
