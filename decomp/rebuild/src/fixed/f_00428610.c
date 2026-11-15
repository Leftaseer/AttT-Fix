/* 0x00428610: updates the ambient sound at the origin (0x00428350 with a zero place); its result. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_00428350(void *self, float *where);

DECOMP(00428610)
unsigned int __thiscall f_00428610(void *this)
{
    float where[3] = { 0.0f, 0.0f, 0.0f };

    return sub_00428350(this, where);
}
