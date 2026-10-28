/* 0x0058C390: vfD8 of the object at +0x204 (a tail call; no stack arguments at its two call sites) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef unsigned int (__thiscall *vfD8_58C390)(void *self);

DECOMP(0058C390)
unsigned int __thiscall f_0058C390(void *this)
{
    void **o = *(void ***)((char *)this + 0x204);
    return ((vfD8_58C390)(*(void ***)o)[0xd8 / 4])(o);
}
