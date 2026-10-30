/* 0x555E60: a constructor: vftable 0x0061BE40, +4 and +8 cleared; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0061BE40[];

DECOMP(00555E60)
void *__thiscall f_00555E60(void *self)
{
    char *this = (char *)self;
    *(void **)this = d_0061BE40;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    return this;
}
