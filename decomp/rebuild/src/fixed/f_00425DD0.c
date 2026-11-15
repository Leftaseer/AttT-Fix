/* 0x00425DD0: the small ActionScript base's constructor: +4 clears, the vtable 0x00607E94, the registry user
 * count (0x006C8738) taken; the first user makes the input singleton the registry (0x006C873C, 0x004215D0).
 * +8 clears.  Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607E94[];
DECOMP_C int d_006C8738;
DECOMP_C void *d_006C873C;
DECOMP_C void *__cdecl sub_004215D0(void);      /* CInput */

DECOMP(00425DD0)
void *__thiscall f_00425DD0(void *this)
{
    char *s = (char *)this;
    *(void **)(s + 4) = 0;
    *(const void **)s = d_00607E94;
    if (d_006C8738 == 0)
        d_006C873C = sub_004215D0();
    d_006C8738++;
    s[8] = 0;
    return s;
}
