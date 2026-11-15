/* 0x00427FF0: builds the pair of cell containers of the object at +0x98: each container's head (0x004C2F40, an empty
 * self-linked list head) goes to +4 and +0x10 and its count to +8 and +0x14; the object is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_004C2F40(void);

DECOMP(00427FF0)
void *__thiscall f_00427FF0(void *this)
{
    char *s = (char *)this;

    *(void **)(s + 4) = sub_004C2F40();
    *(unsigned int *)(s + 8) = 0;
    *(void **)(s + 0x10) = sub_004C2F40();
    *(unsigned int *)(s + 0x14) = 0;
    return s;
}
