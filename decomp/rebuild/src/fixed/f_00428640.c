/* 0x00428640: frees the vector at +0x14 and clears it (+0x14/+0x18/+0x1C). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(00428640)
void __thiscall f_00428640(void *this)
{
    char *s = (char *)this;

    if (*(void **)(s + 0x14) != 0)
        sub_005E3E9C(*(void **)(s + 0x14));
    *(void **)(s + 0x14) = 0;
    *(void **)(s + 0x18) = 0;
    *(void **)(s + 0x1c) = 0;
}
