/* 0x0047A0D0: CMeshObject2DRes ctor: initializes the base (0x4AC0F0), sets the vftable and finishes with
 * 0x479F50; returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC0F0(void *self);
DECOMP_C void __thiscall sub_00479F50(void *self);
DECOMP_C char d_0060EC94[];

DECOMP(0047A0D0)
void *__thiscall f_0047A0D0(void *this)
{
    sub_004AC0F0(this);
    *(char **)this = d_0060EC94;
    sub_00479F50(this);
    return this;
}
