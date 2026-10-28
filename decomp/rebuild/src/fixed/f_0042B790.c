/* 0x0042B790: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(0042B790)
__attribute__((naked)) void __cdecl f_0042B790(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, ecx\n"
        "\tmov ecx, dword ptr [eax + 0x8c]\n"
        "\tmov edx, dword ptr [ecx]\n"
        "\tmov eax, dword ptr [eax + 0x98]\n"
        "\tmov edx, dword ptr [edx + 0xe8]\n"
        "\tmov dword ptr [esp + 4], eax\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
