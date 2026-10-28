/* 0x0057F3F0: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(0057F3F0)
__attribute__((naked)) void __cdecl f_0057F3F0(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx + 0x54]\n"
        "\tmov eax, dword ptr [eax + 4]\n"
        "\tadd ecx, 0x54\n"
        "\tjmp eax\n"
        ".att_syntax prefix\n");
}
