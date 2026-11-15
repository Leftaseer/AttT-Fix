/* 0x004278C0: an nScript handle object: vtable 0x0060826C at +0 with nothing at +4 and +8; returns the object. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060826C[];

DECOMP(004278C0)
void *__thiscall f_004278C0(void *this)
{
    char *s = (char *)this;

    *(void **)(s + 4) = 0;
    *(void **)s = d_0060826C;
    *(void **)(s + 8) = 0;
    return s;
}
