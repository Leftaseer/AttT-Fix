/* 0x00425D20: the constructor of the small object with vtable 0x00607E94: +4 clears and +8 receives the low byte of
 * 0x0046F480's result for the name argument, looked up in the registry at 0x006C873C.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607E94[];
DECOMP_C void *d_006C873C;
DECOMP_C unsigned int __thiscall sub_0046F480(void *registry, void *name);

DECOMP(00425D20)
void *__thiscall f_00425D20(void *this, void *name)
{
    char *s = (char *)this;
    *(unsigned int *)(s + 4) = 0;
    *(const void **)s = d_00607E94;
    s[8] = (char)sub_0046F480(d_006C873C, name);
    return s;
}
