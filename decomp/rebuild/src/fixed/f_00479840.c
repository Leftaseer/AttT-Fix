#include "mesh_position.h"

/* @func 00479840 custom */
DECOMP(00479840)
unsigned int __cdecl f_00479840(char *object, unsigned int eax, unsigned int y_bits)
{
    eax = mesh_position_flags(eax, y_bits);
    object[0x7c] = 1;
    if (mesh_position_uses_default(eax))
        *(float *)(object + 0x78) = *(float *)(object + 0x210);
    else
        __builtin_memcpy(object + 0x78, &y_bits, sizeof(y_bits));
    return eax;
}
