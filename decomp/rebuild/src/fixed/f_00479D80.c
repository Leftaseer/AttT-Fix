#include "mesh_position.h"

/* @func 00479D80 custom */
DECOMP(00479D80)
unsigned int __cdecl f_00479D80(_CMeshObject2DRes *object, unsigned int eax, unsigned int x_bits, unsigned int y_bits)
{
    eax = mesh_position_flags(eax, x_bits);
    if (mesh_position_uses_default(eax)) {
        object->field107_0x74 = object->field513_0x21c;
        object->field108_0x78 = object->field514_0x220;
    } else {
        __builtin_memcpy(&object->field107_0x74, &x_bits, sizeof(x_bits));
        __builtin_memcpy(&object->field108_0x78, &y_bits, sizeof(y_bits));
    }
    object->field509_0x20c = object->field107_0x74 / (*(float *)d_006C895C / *(double *)d_00608858);
    object->field109_0x7c = 1;
    object->field510_0x210 = object->field108_0x78 / (*(float *)d_006C8958 / *(double *)d_00608850);
    return eax;
}
