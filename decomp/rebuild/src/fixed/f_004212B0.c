/* 0x004212B0: releases the object at +0x7C through the deleting destructor in its first vtable slot (flag 1) and
 * clears the field, then destroys the entries of the arrays at +0x94 and +0xA8 (counts +0x98 and +0xAC) from the
 * last one down the same way.  EAX goes in and out as it came (the last destructor's result). */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 004212B0 custom */
typedef unsigned int (__thiscall *scalar_dtor_4212B0)(void *self, int flag);

#define VT(o) (*(void ***)(o))

DECOMP(004212B0)
unsigned int f_004212B0(void *self, unsigned int eax)
{
    char *s = (char *)self;
    void **object = *(void ***)(s + 0x7c);
    unsigned int i;
    if (object) {
        eax = ((scalar_dtor_4212B0)VT(object)[0])(object, 1);
        *(void **)(s + 0x7c) = 0;
    }
    while (*(unsigned int *)(s + 0x98) != 0) {
        *(unsigned int *)(s + 0x98) -= 1;
        i = *(unsigned int *)(s + 0x98);
        object = *(void ***)(*(char **)(s + 0x94) + i * 4);
        if (object)
            eax = ((scalar_dtor_4212B0)VT(object)[0])(object, 1);
    }
    while (*(unsigned int *)(s + 0xac) != 0) {
        *(unsigned int *)(s + 0xac) -= 1;
        i = *(unsigned int *)(s + 0xac);
        object = *(void ***)(*(char **)(s + 0xa8) + i * 4);
        if (object)
            eax = ((scalar_dtor_4212B0)VT(object)[0])(object, 1);
    }
    return eax;
}
