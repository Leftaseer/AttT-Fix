/* 0x0047A120: CMeshObject2DRes ctor: initializes the base (0x4AC0F0), sets the vftable, finishes with 0x479F50
 * and sets the resource with 0x4AB810(name, 0); returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC0F0(void *self);
DECOMP_C void __thiscall sub_00479F50(void *self);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, char shared);
DECOMP_C char d_0060EC94[];

DECOMP(0047A120)
void *__thiscall f_0047A120(void *this, void *name)
{
    sub_004AC0F0(this);
    *(char **)this = d_0060EC94;
    sub_00479F50(this);
    sub_004AB810(this, name, 0);
    return this;
}
