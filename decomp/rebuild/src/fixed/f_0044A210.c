/* 0x0044A210: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(0044A210)
__attribute__((naked)) void __cdecl f_0044A210(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx + 0x8c]\n"
        "\tmov dword ptr [eax + 0x208], 0\n"
        "\tmov ecx, dword ptr [ecx + 0x5c]\n"
        "\tmov edx, dword ptr [ecx]\n"
        "\tmov eax, dword ptr [edx + 0x18]\n"
        "\tjmp eax\n"
        ".att_syntax prefix\n");
}
