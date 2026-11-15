/* 0x00428050: adds a cell to the container at +4: 0x005AD6C0 finds or makes the node for the key (given the container
 * and its head), the owning grid is told (0x004E0EF0 with 1), the container takes the node as its head and the node is
 * linked back as its predecessor's successor. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005AD6C0(void *container, void *head, void *key);
DECOMP_C void __thiscall sub_004E0EF0(void *self, int a);

DECOMP(00428050)
void __thiscall f_00428050(void *this, unsigned int key)
{
    char *s = (char *)this;
    char *container = *(char **)(s + 4);
    char *node = (char *)sub_005AD6C0(container, *(void **)(container + 4), &key);

    sub_004E0EF0(s, 1);
    *(char **)(container + 4) = node;
    **(char ***)(node + 4) = node;
}
