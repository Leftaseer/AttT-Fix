/* 0x0054C680: a delegate callback (fn(ctx in ECX, a, b), pop 8): releases the object held at +0x59C (vtable slot 0
 * with 1), copies *b to *a, then chains to the delegate at +0x400 with that delegate as both arguments */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef unsigned int (__thiscall *dlg_54C680)(void *ctx, void *a, void *b);

DECOMP(0054C680)
unsigned int __thiscall f_0054C680(void *this, unsigned int *a, unsigned int *b)
{
    char *self = (char *)this;
    void **held = *(void ***)(self + 0x59c);
    char *d;
    if (held)
        ((void (__thiscall *)(void *, int))(*(void ***)held)[0])(held, 1);
    *a = *b;
    d = self + 0x400;
    return (*(dlg_54C680 *)(d + 8))(*(void **)(d + 0xc), d, d);
}
