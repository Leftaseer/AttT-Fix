/* 0x00520380: Cramer's rule: out[i] = det with column i replaced (0x00520020 takes three column indices, 3 = the
 * constants) / det(0, 1, 2) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C float __thiscall sub_00520020(void *self, int c0, int c1, int c2);

DECOMP(00520380)
void __thiscall f_00520380(void *this, float *out)
{
    float d = sub_00520020(this, 0, 1, 2);
    out[0] = sub_00520020(this, 3, 1, 2) / d;
    out[1] = sub_00520020(this, 0, 3, 2) / d;
    out[2] = sub_00520020(this, 0, 1, 3) / d;
}
