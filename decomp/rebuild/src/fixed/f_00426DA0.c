/* 0x00426DA0: removes the list node at +0x5C whose payload (+8) is the argument, unlinking it and freeing it.  A
 * missing payload leaves the list untouched. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00426DA0)
void __thiscall f_00426DA0(void *this, void *object)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 0x5c);
    char *node = *(char **)head;

    if (node == head)
        return;
    while (*(void **)(node + 8) != object) {
        node = *(char **)node;
        if (node == head)
            return;
    }
    if (node != head) {
        *(char **)(*(char **)(node + 4)) = *(char **)node;
        *(char **)(*(char **)node + 4) = *(char **)(node + 4);
        sub_005E3E9C(node);
        *(unsigned int *)(s + 0x60) -= 1;
    }
}
