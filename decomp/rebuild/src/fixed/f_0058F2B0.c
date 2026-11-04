#include "auto_pre.h"

DECOMP_C char d_0060984C[];

/* @func 0058F2B0 */
DECOMP(0058F2B0)
unsigned int __stdcall f_0058F2B0(const float *a, const float *b, const float *c)
{
    float cx = GH_FROUND(c[0] - b[0]);
    float cy = GH_FROUND(c[1] - b[1]);
    float ax = GH_FROUND(a[0] - b[0]);
    float ay = GH_FROUND(a[1] - b[1]);
    float cross = GH_FROUND(ay * cx - cy * ax);
    // The native JA rejects only an ordered value above the threshold.
    return !(cross > *(float *)d_0060984C);
}
