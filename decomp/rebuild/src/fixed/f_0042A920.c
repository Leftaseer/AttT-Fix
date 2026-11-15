/* 0x0042A920: forwards two arguments to slot 0x38 of the driven object at +0x1C4. */
/* @conv ECX 8 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A920)(void *self, unsigned int a, unsigned int b);

DECOMP(0042A920)
int __thiscall f_0042A920(char *this, unsigned int a, unsigned int b)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A920)(*(void ***)driven)[0x38 / 4])(driven, a, b);
}
