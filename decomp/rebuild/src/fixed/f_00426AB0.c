/* 0x00426AB0: the alpha button's control destructor: the vtables 0x00608188 and 0x0060809C, then the 2D mesh part
 * (+0x54) and the 3D control are destroyed. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608188[], d_0060809C[];
DECOMP_C void __thiscall sub_00479660(void *self);
DECOMP_C void __thiscall sub_00442960(void *self);

DECOMP(00426AB0)
void __thiscall f_00426AB0(void *this)
{
    char *s = (char *)this;
    *(const void **)s = d_00608188;
    *(const void **)(s + 0x54) = d_0060809C;
    sub_00479660(s + 0x54);
    sub_00442960(s);
}
