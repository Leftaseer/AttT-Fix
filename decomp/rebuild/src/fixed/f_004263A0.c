/* 0x004263A0: the alpha button's constructor: the control base 0x00426A00 with the three arguments, then the
 * vtable 0x00608078 and the 2D part's vtable 0x00607F8C at +0x54.  Returns this. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_00608078[], d_00607F8C[];
DECOMP_C void __thiscall sub_00426A00(void *self, void *a, void *b, void *c);

DECOMP(004263A0)
void *__thiscall f_004263A0(void *this, void *a, void *b, void *c)
{
    char *s = (char *)this;
    sub_00426A00(s, a, b, c);
    *(const void **)s = d_00608078;
    *(const void **)(s + 0x54) = d_00607F8C;
    return s;
}
