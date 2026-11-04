#include "mesh_position.h"

/* @func 004797D0 custom */
DECOMP(004797D0)
unsigned int __cdecl f_004797D0(char *object, unsigned int eax, unsigned int x_bits, unsigned int y_bits)
{
    eax = mesh_position_flags(eax, x_bits);
    object[0x7c] = 1;
    if (mesh_position_uses_default(eax)) {
        *(float *)(object + 0x74) = *(float *)(object + 0x20c);
        *(float *)(object + 0x78) = *(float *)(object + 0x210);
    } else {
        __builtin_memcpy(object + 0x74, &x_bits, sizeof(x_bits));
        __builtin_memcpy(object + 0x78, &y_bits, sizeof(y_bits));
    }
    return eax;
}
