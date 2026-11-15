/* 0x00426890: a thunk that jumps to the virtual at +0xd4 with its caller's arguments (the original instructions;
 * build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(00426890)
__attribute__((naked)) void __cdecl f_00426890(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx]\n"
        "\tmov edx, dword ptr [eax + 0xd4]\n"
        "\tjmp edx\n"
        ".att_syntax prefix\n");
}
