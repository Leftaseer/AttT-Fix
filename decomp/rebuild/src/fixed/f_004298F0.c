/* 0x004298F0: clears the map held at +4: frees the root subtree (0x004293F0), turns the head back into an empty
 * circle (its +4 parent, +0 and +8 links at itself) and clears the count at +8. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004293F0(void *self, char *node);

DECOMP(004298F0)
void __thiscall f_004298F0(void *this)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 4);

    sub_004293F0(s, *(char **)(head + 4));
    *(char **)(head + 4) = head;
    *(unsigned int *)(s + 8) = 0;
    *(char **)head = head;
    *(char **)(head + 8) = head;
}
