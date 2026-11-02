/* 0x004CC8D0: dispatch the first virtual method with this in ECX and argument 1.
 * Reuse our stack argument and tail-jump, so the method's ret 4 reaches our caller.
 * A C function containing only a final inline-asm jmp did not constrain ECX;
 * clang left it at the caller's value, crashing even with a valid thiscall target.
 * Keep the complete ABI boundary explicit, including the null path and EDX target. */
/* @raw */
#include "auto_pre.h"

DECOMP(004CC8D0)
__attribute__((naked)) void __stdcall f_004CC8D0(undefined4 *param_1)
{
    __asm__(".intel_syntax noprefix\n"
        "\tmov ecx, dword ptr [esp + 4]\n"
        "\ttest ecx, ecx\n"
        "\tjz 1f\n"
        "\tmov eax, dword ptr [ecx]\n"
        "\tmov edx, dword ptr [eax]\n"
        "\tmov dword ptr [esp + 4], 1\n"
        "\tjmp edx\n"
        "1:\n"
        "\tret 4\n"
        ".att_syntax prefix\n");
}
