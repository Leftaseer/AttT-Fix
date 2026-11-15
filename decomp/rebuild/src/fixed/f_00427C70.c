/* 0x00427C70: clears the two map containers at +4 and +0x10 (each held by its head node): the head links point at
 * themselves, the count (+8 / +0x14) goes to zero and the nodes threaded off the head's left link are deleted. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);

static void clear_427C70(char *head, unsigned int *count)
{
    char *p = *(char **)head;

    *(char **)head = head;
    *(char **)(head + 4) = head;
    *count = 0;
    while (p != head) {
        char *next = *(char **)p;
        sub_005E3E9C(p);
        p = next;
    }
}

DECOMP(00427C70)
void __thiscall f_00427C70(void *this)
{
    char *s = (char *)this;

    clear_427C70(*(char **)(s + 4), (unsigned int *)(s + 8));
    clear_427C70(*(char **)(s + 0x10), (unsigned int *)(s + 0x14));
}
