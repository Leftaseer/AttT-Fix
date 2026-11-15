/* 0x00422160: the destructor of the 2D scene.  It puts its two vtables in (+0 = 0x00607C44, +4 = 0x00607C24), has
 * 0x004212B0 release the collector state on this+4, deletes the objects at +0x84 and +0x88 through the deleting
 * destructor in their first vtable slot (flag 1), frees the arrays at +0xAC (after storing vtable 0x00607B74 at
 * +0xA8) and at +0x98 (after 0x00607B6C at +0x94) with the operator delete 0x005E3EBA, and closes with the base
 * destructor 0x004B2010. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607C44[];
DECOMP_C char d_00607C24[];
DECOMP_C char d_00607B74[];
DECOMP_C char d_00607B6C[];
DECOMP_C unsigned int __cdecl sub_004212B0(void *self, unsigned int eax);
DECOMP_C void __cdecl sub_005E3EBA(void *block);
DECOMP_C void __thiscall sub_004B2010(void *self);
typedef unsigned int (__thiscall *dtor_422160)(void *self, int flag);

DECOMP(00422160)
void __thiscall f_00422160(void *self)
{
    char *s = (char *)self;
    void **o;
    *(const void **)s = d_00607C44;
    *(const void **)(s + 4) = d_00607C24;
    sub_004212B0(s + 4, 0);
    o = *(void ***)(s + 0x84);
    if (o) {
        ((dtor_422160)(*(void ***)o)[0])(o, 1);
        *(void **)(s + 0x84) = 0;
    }
    o = *(void ***)(s + 0x88);
    if (o) {
        ((dtor_422160)(*(void ***)o)[0])(o, 1);
        *(void **)(s + 0x88) = 0;
    }
    *(const void **)(s + 0xa8) = d_00607B74;
    if (*(void **)(s + 0xac)) {
        sub_005E3EBA(*(void **)(s + 0xac));
        *(void **)(s + 0xac) = 0;
    }
    *(const void **)(s + 0x94) = d_00607B6C;
    if (*(void **)(s + 0x98)) {
        sub_005E3EBA(*(void **)(s + 0x98));
        *(void **)(s + 0x98) = 0;
    }
    sub_004B2010(s);
}
