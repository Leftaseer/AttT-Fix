/* 0x00425240: C3DControlsManager::RemoveControl: walks the ring whose sentinel sits at +0x40 looking for the node
 * whose id (+8) is the argument; a found node is unlinked (its neighbours point around it), freed with the
 * MSVCR80 operator delete and the count at +0x44 drops by one.  Nothing is done when no node has the id. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block); /* operator delete */

DECOMP(00425240)
void __thiscall f_00425240(void *this, int id)
{
    char *s = (char *)this;
    void **sentinel = *(void ***)(s + 0x40);
    void *node = *sentinel;
    if (node == sentinel)
        return;
    for (;;) {
        if (*(int *)((char *)node + 8) == id) {
            if (node != sentinel) {
                void *prev = *(void **)((char *)node + 4);
                void *next = *(void **)node;
                *(void **)prev = next;
                *(void **)((char *)next + 4) = prev;
                sub_005E3E9C(node);
                *(int *)(s + 0x44) -= 1;
            }
            return;
        }
        node = *(void **)node;
        if (node == sentinel)
            return;
    }
}
