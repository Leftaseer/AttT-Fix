/* 0x004268A0: the alpha button's vtable reset: 0x00608078 for the control and 0x00607F8C for the 2D part (+0x54),
 * then the control destructor. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608078[], d_00607F8C[];
DECOMP_C void __thiscall sub_00426AB0(void *self);

DECOMP(004268A0)
void __thiscall f_004268A0(void *this)
{
    char *s = (char *)this;
    *(const void **)s = d_00608078;
    *(const void **)(s + 0x54) = d_00607F8C;
    sub_00426AB0(s);
}
