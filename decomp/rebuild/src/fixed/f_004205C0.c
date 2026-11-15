/* 0x004205C0: a thunk that passes the call on to a function pointer taken from the member at this+4 (+4 of that
 * member), with ECX advanced to the member: the original instructions, a naked function that takes the
 * original's place as is */
/* @raw */
#include "auto_pre.h"

DECOMP(004205C0)
__attribute__((naked)) void __cdecl f_004205C0(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx + 4]\n"
        "\tmov eax, dword ptr [eax + 4]\n"
        "\tadd ecx, 4\n"
        "\tjmp eax\n"
        ".att_syntax prefix\n");
}
