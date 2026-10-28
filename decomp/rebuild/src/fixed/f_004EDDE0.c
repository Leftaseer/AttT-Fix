/* 0x004EDDE0: removes the finished children: every element of the list at +0x4C whose vf20 says it is done is
 * deleted (scalar deleting destructor) and its node unlinked and freed (count at +0x50) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *p);
typedef char (__thiscall *vf20_4EDDE0)(void *self);
typedef void (__thiscall *dtor_4EDDE0)(void *self, int flags);

DECOMP(004EDDE0)
void __thiscall f_004EDDE0(void *this)
{
    char *s = (char *)this;
    void **head = *(void ***)(s + 0x4c);
    void **node = (void **)*head;
    while (node != head) {
        void **o = (void **)node[2];
        if (((vf20_4EDDE0)(*(void ***)o)[0x20 / 4])(o)) {
            node = (void **)*node;
        } else {
            void **next;
            o = (void **)node[2];
            if (o)
                ((dtor_4EDDE0)(*(void ***)o)[0])(o, 1);
            next = (void **)*node;
            if (node != *(void ***)(s + 0x4c)) {
                *(void ***)node[1] = next;
                ((void **)*node)[1] = node[1];
                sub_005E3E9C(node);
                *(int *)(s + 0x50) += -1;
            }
            node = next;
        }
    }
}
