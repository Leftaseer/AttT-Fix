/* 0x00428710: frees the vector at +0x24 and clears it (+0x24/+0x28/+0x2C). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(00428710)
void __thiscall f_00428710(void *this)
{
    char *s = (char *)this;

    if (*(void **)(s + 0x24) != 0)
        sub_005E3E9C(*(void **)(s + 0x24));
    *(void **)(s + 0x24) = 0;
    *(void **)(s + 0x28) = 0;
    *(void **)(s + 0x2c) = 0;
}
