/* Lua_006C70B0::OnCancel 0x00563A90: a thunk that passes the call on through a vftable (its arguments, ECX and
 * the stack as the caller left them, go to the callee, which pops them; the decompiler cannot tell how many there
 * are, C cannot pass "the same arguments" on): the original instructions, a naked function that takes the
 * original's place as is (build.py: no adapter) */
/* @raw */
#include "auto_pre.h"

DECOMP(00563A90)
__attribute__((naked)) void __cdecl f_00563A90(void)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov eax, dword ptr [ecx]\n"
        "\tjmp dword ptr [eax + 0x44]\n"
        ".att_syntax prefix\n");
}
