/* 0x00536EA0: 0x004AC890 on the object, then a tail call of vf C0 of its +0x204 (whatever arguments the caller
 * left on the stack go on to that function, which pops them; C cannot pass "the same arguments" on, and nothing in
 * the game calls or points to this function, so their number is unknown): the original instructions, a naked
 * function that takes the original's place as is */
/* @raw */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC890(void *self);

DECOMP(00536EA0)
__attribute__((naked)) void __cdecl f_00536EA0(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tpush esi\n"
        "\tmov esi, ecx\n"
        "\tcall %P0\n"
        "\tmov ecx, dword ptr [esi + 0x204]\n"
        "\tmov eax, dword ptr [ecx]\n"
        "\tpop esi\n"
        "\tmov eax, dword ptr [eax + 0xc0]\n"
        "\tjmp eax\n"
        ".att_syntax prefix\n" :: "i"(sub_004AC890));
}
