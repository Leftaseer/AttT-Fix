/* 0x0044A210: renders the scene for a screenshot: +0x208 of the object at +0x8C cleared, then vf18 of the one at
 * +0x5C (a tail call; no stack arguments at its one call site) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef unsigned int (__thiscall *vf18_44A210)(void *self);

DECOMP(0044A210)
unsigned int __thiscall f_0044A210(void *this)
{
    char *s = (char *)this;
    void **o;
    *(unsigned int *)(*(char **)(s + 0x8c) + 0x208) = 0;
    o = *(void ***)(s + 0x5c);
    return ((vf18_44A210)(*(void ***)o)[0x18 / 4])(o);
}
