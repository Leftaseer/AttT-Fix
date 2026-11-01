/* 0x00480410: sub_004802D0 writes its float out-param over the caller's first argument slot; the decompiler read
 * the pointer bits as a float and re-read the clobbered pointer for the second call.  The first range test is a
 * pair of SSE comiss/ja (0 vs slot, slot vs 0x68AE40): unordered takes neither branch, so a NaN result from the
 * first call still goes on to the second; the x87 test after it (fcomip slot, 0) sends a NaN to 4. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C undefined4 __thiscall sub_004802D0(void *p0, float *p1, float *p2);
DECOMP_C char d_0068AE40[];

DECOMP(00480410)
int __thiscall f_00480410(void *this, float *param_1, float *param_2)
{
    float *a = param_1;
    float *slot = (float *)&param_1;      /* the first call stores its result here */
    int r = sub_004802D0(a, this, slot);

    if (r == 0 || r == 1) return r;
    if (!(*slot < 0.0f) && !(*slot > *(float *)d_0068AE40)) {
        sub_004802D0(this, a, param_2);
        *slot = *param_2;                 /* fld [param_2]; fstp [the first argument slot] */
        if ((0.0f <= *slot) && (*slot <= *(float *)d_0068AE40)) return 3;
    }
    return 4;
}
