/* 0x0058C3C0: 0x004AC890, then on the object at +0x204: vf28(+0x3C), vf30(10), and a tail call of vf28 with the
 * caller's own argument (so this function pops what vf28 pops: one argument) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC890(void *self);
typedef unsigned int (__thiscall *vf_1arg_58C3C0)(void *self, unsigned int a);

DECOMP(0058C3C0)
unsigned int __thiscall f_0058C3C0(void *this, unsigned int a)
{
    char *self = (char *)this;
    void **o;
    sub_004AC890(this);
    o = *(void ***)(self + 0x204);
    ((vf_1arg_58C3C0)(*(void ***)o)[0x28 / 4])(o, *(unsigned int *)(self + 0x3c));
    o = *(void ***)(self + 0x204);
    ((vf_1arg_58C3C0)(*(void ***)o)[0xc0 / 4])(o, 10);
    o = *(void ***)(self + 0x204);
    return ((vf_1arg_58C3C0)(*(void ***)o)[0x28 / 4])(o, a);
}
