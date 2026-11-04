#include "mesh_position.h"

/* @func 00479DF0 custom */
DECOMP(00479DF0)
unsigned int __cdecl f_00479DF0(_CMeshObject2DRes *object, unsigned int eax, unsigned int x_bits)
{
    eax = mesh_position_flags(eax, x_bits);
    if (mesh_position_uses_default(eax))
        object->field107_0x74 = object->field513_0x21c;
    else
        __builtin_memcpy(&object->field107_0x74, &x_bits, sizeof(x_bits));
    object->field109_0x7c = 1;
    object->field509_0x20c = object->field107_0x74 / (*(float *)d_006C895C / *(double *)d_00608858);
    return eax;
}
