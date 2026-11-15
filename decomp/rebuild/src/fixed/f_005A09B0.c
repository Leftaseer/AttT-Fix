/* 0x005A09B0: D3DPERF_BeginEvent through the lazily resolved d3d9.dll export at 0x8D1290 (resolved by
 * 0x5A0870, whose answer is only meaningful in AL).  -1 means that the profiler is not available. */
/* @conv EAX 8 */
/* @func 005A09B0 custom */
#include "auto_pre.h"
DECOMP_C unsigned char __cdecl sub_005A0870(void *eax_in);
typedef int (__stdcall *fp_5A09B0)(unsigned int color, void *name);
DECOMP_C char d_008D1290[];

DECOMP(005A09B0)
int __cdecl f_005A09B0(void *in_eax, unsigned int color, void *name)
{
    fp_5A09B0 begin;

    if (!sub_005A0870(in_eax))
        return -1;
    begin = *(fp_5A09B0 *)d_008D1290;
    if (!begin)
        return -1;
    return begin(color, name);
}
