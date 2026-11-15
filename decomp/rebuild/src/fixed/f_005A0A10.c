/* 0x005A0A10: D3DPERF_SetRegion through the lazily resolved d3d9.dll export at 0x8D129C (resolved by 0x5A0870,
 * whose answer is only meaningful in AL).  0 means that the profiler is not available. */
/* @conv EAX 8 */
/* @func 005A0A10 custom */
#include "auto_pre.h"
DECOMP_C unsigned char __cdecl sub_005A0870(void *eax_in);
typedef int (__stdcall *fp_5A0A10)(unsigned int color, void *name);
DECOMP_C char d_008D129C[];

DECOMP(005A0A10)
int __cdecl f_005A0A10(void *in_eax, unsigned int color, void *name)
{
    fp_5A0A10 region;

    if (!sub_005A0870(in_eax))
        return 0;
    region = *(fp_5A0A10 *)d_008D129C;
    if (!region)
        return 0;
    return region(color, name);
}
