/* shared_vf_nEvent_Event_AddInfoEventMsg__ObjectListener_CWorldLevel__1 0x0053C3A0: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(0053C3A0)
__attribute__((naked)) void __cdecl f_0053C3A0(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, ecx\n"
        "\tmov ecx, dword ptr [eax + 0x14]\n"
        "\tadd ecx, dword ptr [eax + 8]\n"
        "\tmov edx, dword ptr [eax + 0x10]\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
