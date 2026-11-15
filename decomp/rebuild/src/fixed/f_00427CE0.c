/* 0x00427CE0: hands a float down a tree of objects that keep two child maps (+4 and +0x10, each held by its head
 * node): every child of the first map is asked for its present value through its virtual +0x1C, gets the argument
 * stored at +0x2C and is told the old value through its virtual +0x18 (with 1); the children of the second map are
 * recursed into.  The register argument in EAX is only carried along. */
/* @func 00427CE0 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

static void apply_float(void *self, unsigned int reg_eax, float value)
{
    char *s = (char *)self;
    char *first = *(char **)(s + 4);
    char *second = *(char **)(s + 0x10);
    char *n;

    for (n = *(char **)first; n != first; n = *(char **)n) {
        void *child = *(void **)(n + 8);
        void **vtable = *(void ***)child;
        float old = ((float (__thiscall *)(void *))vtable[7])(child);
        *(float *)((char *)child + 0x2c) = value;
        ((void (__thiscall *)(void *, float, int))vtable[6])(child, old, 1);
    }
    for (n = *(char **)second; n != second; n = *(char **)n)
        apply_float(*(void **)(n + 8), reg_eax, value);
}

DECOMP(00427CE0)
void __cdecl f_00427CE0(void *self, unsigned int reg_eax, float value)
{
    apply_float(self, reg_eax, value);
}
