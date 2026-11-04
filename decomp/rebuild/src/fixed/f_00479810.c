#include "mesh_position.h"

/* @func 00479810 custom */
DECOMP(00479810)
unsigned int __cdecl f_00479810(char *object, unsigned int eax, unsigned int x_bits)
{
    eax = mesh_position_flags(eax, x_bits);
    object[0x7c] = 1;
    if (mesh_position_uses_default(eax))
        *(float *)(object + 0x74) = *(float *)(object + 0x20c);
    else
        __builtin_memcpy(object + 0x74, &x_bits, sizeof(x_bits));
    return eax;
}
