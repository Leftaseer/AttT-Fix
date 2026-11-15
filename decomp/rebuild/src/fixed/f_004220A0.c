/* 0x004220A0: the destructor of the script table.  It takes its own vtable (0x00607CC4), releases the count at +8
 * through 0x00402270 (the global object held at 0x008D122C, -10000 and the count) when it is positive and sets it
 * to -1, then switches to the base vtable (0x00607CB8) and runs the base destructor 0x00422000, whose result is
 * returned. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607CC4[];   /* vftable */
DECOMP_C char d_00607CB8[];   /* vftable */
DECOMP_C void *d_008D122C;    /* the object the release goes to */
DECOMP_C void __cdecl sub_00402270(void *object, int code, int count);
DECOMP_C unsigned int __thiscall sub_00422000(void *self);

DECOMP(004220A0)
unsigned int __thiscall f_004220A0(void *self)
{
    char *s = (char *)self;
    int count;
    *(const void **)s = d_00607CC4;
    count = *(int *)(s + 8);
    if (count > 0) {
        sub_00402270(d_008D122C, -10000, count);
        *(int *)(s + 8) = -1;
    }
    *(const void **)s = d_00607CB8;
    return sub_00422000(s);
}
