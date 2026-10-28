/* 0x004AC650: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(004AC650)
__attribute__((naked)) void __cdecl f_004AC650(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov ecx, dword ptr [esp + 4]\n"
        "\tmov dword ptr [ecx + 0x1bc], 0\n"
        "\tmov eax, dword ptr [ecx]\n"
        "\tmov edx, dword ptr [eax]\n"
        "\tmov dword ptr [esp + 4], 1\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
