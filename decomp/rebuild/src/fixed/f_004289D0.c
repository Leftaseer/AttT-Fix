/* 0x004289D0: destroys a sound record: frees the vector at +0x24, clears it and, when the low bit of the flag is
 * set, deletes the object; the object is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(004289D0)
void *__thiscall f_004289D0(void *this, unsigned char flag)
{
    char *s = (char *)this;

    if (*(void **)(s + 0x24) != 0)
        sub_005E3E9C(*(void **)(s + 0x24));
    *(void **)(s + 0x24) = 0;
    *(void **)(s + 0x28) = 0;
    *(void **)(s + 0x2c) = 0;
    if (flag & 1)
        sub_005E3E9C(s);
    return s;
}
