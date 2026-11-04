#include "mesh_position.h"

/* @func 00479E40 custom */
DECOMP(00479E40)
unsigned int __cdecl f_00479E40(_CMeshObject2DRes *object, unsigned int eax, unsigned int y_bits)
{
    eax = mesh_position_flags(eax, y_bits);
    if (mesh_position_uses_default(eax))
        object->field108_0x78 = object->field514_0x220;
    else
        __builtin_memcpy(&object->field108_0x78, &y_bits, sizeof(y_bits));
    object->field109_0x7c = 1;
    object->field510_0x210 = object->field108_0x78 / (*(float *)d_006C8958 / *(double *)d_00608850);
    return eax;
}
