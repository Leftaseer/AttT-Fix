/* 0x0042B100: the height difference of the loop's two ends (the +0x204 key's z minus the +0x208 key's z). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042B100)
float __thiscall f_0042B100(char *this)
{
    const float *keys = *(const float **)(this + 0x1d8);
    return keys[*(unsigned int *)(this + 0x204) * 3 + 2] - keys[*(unsigned int *)(this + 0x208) * 3 + 2];
}
