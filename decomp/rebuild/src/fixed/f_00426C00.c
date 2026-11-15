/* 0x00426C00: empties the list at +0x5C (the sentinel points at itself in both directions), clears the +0x60 count
 * and frees every former node. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00426C00)
void __thiscall f_00426C00(void *this)
{
    char *s = (char *)this;
    unsigned int *head = *(unsigned int **)(s + 0x5c);
    unsigned int *node = (unsigned int *)*head;

    *head = (unsigned int)head;
    head = *(unsigned int **)(s + 0x5c);
    head[1] = (unsigned int)head;
    *(unsigned int *)(s + 0x60) = 0;
    while (node != *(unsigned int **)(s + 0x5c)) {
        unsigned int *next = (unsigned int *)*node;
        sub_005E3E9C(node);
        node = next;
    }
}
