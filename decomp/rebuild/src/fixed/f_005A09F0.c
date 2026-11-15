/* 0x005A09F0: D3DPERF_SetMarker through the lazily resolved d3d9.dll export at 0x8D1298 (resolved by 0x5A0870,
 * whose answer is only meaningful in AL).  0 means that the profiler is not available. */
/* @conv EAX 8 */
/* @func 005A09F0 custom */
#include "auto_pre.h"
DECOMP_C unsigned char __cdecl sub_005A0870(void *eax_in);
typedef int (__stdcall *fp_5A09F0)(unsigned int color, void *name);
DECOMP_C char d_008D1298[];

DECOMP(005A09F0)
int __cdecl f_005A09F0(void *in_eax, unsigned int color, void *name)
{
    fp_5A09F0 marker;

    if (!sub_005A0870(in_eax))
        return 0;
    marker = *(fp_5A09F0 *)d_008D1298;
    if (!marker)
        return 0;
    return marker(color, name);
}
