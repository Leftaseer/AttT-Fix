/* 0x00429B10: erases the whole map held by its head pointer at +4 (0x00429920 from the first node to the head, the
 * resulting iterator left in a local the call can use), frees the head and clears +4/+8. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00429920(void *self, char **out, char *first, char *last);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */

DECOMP(00429B10)
void __thiscall f_00429B10(void *this)
{
    char *s = (char *)this;
    char *out;
    char **head = *(char ***)(s + 4);

    sub_00429920(s, &out, *head, (char *)head);
    sub_005E3E9C(head);
    *(void **)(s + 4) = 0;
    *(void **)(s + 8) = 0;
}
