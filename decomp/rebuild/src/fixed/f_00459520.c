/* 0x00459520: toggles the flag at +0x38 and calls vf64 of the four members at +0x294, +0x4E8, +0x73C and +0x990
 * (the last one a tail call; its result is returned) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef unsigned int (__thiscall *vf64_459520)(void *self);

DECOMP(00459520)
unsigned int __thiscall f_00459520(void *this)
{
    char *s = (char *)this;
    void **m;
    s[0x38] = s[0x38] == 0;
    m = (void **)(s + 0x294); ((vf64_459520)(*(void ***)m)[0x64 / 4])(m);
    m = (void **)(s + 0x4e8); ((vf64_459520)(*(void ***)m)[0x64 / 4])(m);
    m = (void **)(s + 0x73c); ((vf64_459520)(*(void ***)m)[0x64 / 4])(m);
    m = (void **)(s + 0x990);
    return ((vf64_459520)(*(void ***)m)[0x64 / 4])(m);
}
