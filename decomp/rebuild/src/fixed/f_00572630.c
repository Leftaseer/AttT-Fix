/* shared_vf_nEvent_Event_evCreatureInfo__ObjectListener_CStandard_ReCallEventDefense__1 0x00572630: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(00572630)
__attribute__((naked)) void __cdecl f_00572630(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, ecx\n"
        "\tmov ecx, dword ptr [eax + 8]\n"
        "\tmov edx, dword ptr [eax + 0xc]\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
