/* 0x005A0990: Direct3DCreate9 through the lazily resolved d3d9.dll export at 0x8D128C (resolved by 0x5A0870).
 * 0x5A0870 answers in AL (only AL is meaningful); a missing d3d9.dll or export yields NULL. */
/* @conv EAX 4 */
/* @func 005A0990 custom */
#include "auto_pre.h"
DECOMP_C unsigned char __cdecl sub_005A0870(void *eax_in);
typedef void *(__stdcall *fp_5A0990)(unsigned int version);
DECOMP_C char d_008D128C[];

DECOMP(005A0990)
void *__cdecl f_005A0990(void *in_eax, unsigned int version)
{
    fp_5A0990 create;

    if (!sub_005A0870(in_eax))
        return 0;
    create = *(fp_5A0990 *)d_008D128C;
    if (!create)
        return 0;
    return create(version);
}
