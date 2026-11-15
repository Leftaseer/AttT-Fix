/* 0x005A0A50: D3DPERF_SetOptions through the lazily resolved d3d9.dll export at 0x8D12A4 (resolved by 0x5A0870,
 * whose answer is only meaningful in AL).  0 means that the profiler is not available. */
/* @conv EAX 4 */
/* @func 005A0A50 custom */
#include "auto_pre.h"
DECOMP_C unsigned char __cdecl sub_005A0870(void *eax_in);
typedef int (__stdcall *fp_5A0A50)(unsigned int options);
DECOMP_C char d_008D12A4[];

DECOMP(005A0A50)
int __cdecl f_005A0A50(void *in_eax, unsigned int options)
{
    fp_5A0A50 set_options;

    if (!sub_005A0870(in_eax))
        return 0;
    set_options = *(fp_5A0A50 *)d_008D12A4;
    if (!set_options)
        return 0;
    return set_options(options);
}
