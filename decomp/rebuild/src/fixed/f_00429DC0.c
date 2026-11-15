/* 0x00429DC0: makes the map at +4: a 0x34-byte head node (0x00427C00) with the header flag +0x31 set, all three
 * links pointing at itself, and the count at +8 = 0. Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00427C00(void);

DECOMP(00429DC0)
void *__thiscall f_00429DC0(void *this)
{
    char *s = (char *)this;
    char *head = sub_00427C00();

    *(char **)(s + 4) = head;
    head[0x31] = 1;
    *(char **)(head + 4) = head;
    *(char **)head = head;
    *(char **)(head + 8) = head;
    *(void **)(s + 8) = 0;
    return s;
}
