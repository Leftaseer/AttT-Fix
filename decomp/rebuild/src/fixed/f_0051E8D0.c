/* 0x0051E8D0: up to n + 1 times calls vf80 of the first child (list at +0xB0, element at +8) while the list is not
 * empty; a call returning nonzero goes back to look at the list again */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef char (__thiscall *vf80_51E8D0)(void *self);

DECOMP(0051E8D0)
void __thiscall f_0051E8D0(void *this, int n)
{
    while (n >= 0) {
        char **head = *(char ***)((char *)this + 0xb0);
        char *node = *head;
        if (node == (char *)head)
            return;
        for (;;) {
            void **o = *(void ***)(node + 8);
            n--;
            if (((vf80_51E8D0)(*(void ***)o)[0x80 / 4])(o))
                break;
            if (n < 0)
                return;
        }
    }
}
