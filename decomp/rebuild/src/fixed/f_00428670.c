/* 0x00428670: frees the vector at +0x18 and clears it (+0x18/+0x1C/+0x20). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(00428670)
void __thiscall f_00428670(void *this)
{
    char *s = (char *)this;

    if (*(void **)(s + 0x18) != 0)
        sub_005E3E9C(*(void **)(s + 0x18));
    *(void **)(s + 0x18) = 0;
    *(void **)(s + 0x1c) = 0;
    *(void **)(s + 0x20) = 0;
}
