/* 0x0056BA80: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(0056BA80)
__attribute__((naked)) void __cdecl f_0056BA80(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx + 8]\n"
        "\tmov ecx, dword ptr [eax + 4]\n"
        "\tmov ecx, dword ptr [ecx + 8]\n"
        "\tmov edx, dword ptr [ecx]\n"
        "\tmov edx, dword ptr [edx + 0xd8]\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
