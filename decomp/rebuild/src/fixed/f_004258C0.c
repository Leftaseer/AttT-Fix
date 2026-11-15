/* 0x004258C0: asks the object at +0x1C4, through slot 0x2C of its vtable (the vtable itself in ECX), for a
 * 24-byte record - the address comes back in the local; the three arguments go to record+0xC, +0x10 and +0x14
 * and slot 0x30 of the vtable finishes the object.  A negative result from the first slot is returned as is. */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef int (__thiscall *vf_4258C0_begin)(void *self, void *object, int zero, int size, void **out, int zero2);
typedef int (__stdcall *vf_4258C0_end)(void *object);

DECOMP(004258C0)
int __thiscall f_004258C0(char *this, unsigned int a, unsigned int b, unsigned int c)
{
    void *object = *(void **)(this + 0x1c4);
    void *vtable = *(void **)object;
    void *out = 0;
    int result = ((vf_4258C0_begin)(((void **)vtable)[0x2c / 4]))(vtable, object, 0, 0x18, &out, 0);

    if (result < 0)
        return result;
    *(unsigned int *)((char *)out + 0xc) = a;
    *(unsigned int *)((char *)out + 0x10) = b;
    *(unsigned int *)((char *)out + 0x14) = c;
    object = *(void **)(this + 0x1c4);
    vtable = *(void **)object;
    return ((vf_4258C0_end)(((void **)vtable)[0x30 / 4]))(object);
}
