/* 0x004269B0: the alpha button's deleting destructor: the control vtables, the destructor, then the delete if the
 * flag says so.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608078[], d_00607F8C[];
DECOMP_C void __thiscall sub_00426AB0(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(004269B0)
void *__thiscall f_004269B0(void *this, unsigned int flags)
{
    char *s = (char *)this;
    *(const void **)s = d_00608078;
    *(const void **)(s + 0x54) = d_00607F8C;
    sub_00426AB0(s);
    if (flags & 1)
        sub_005E3E9C(s);
    return s;
}
