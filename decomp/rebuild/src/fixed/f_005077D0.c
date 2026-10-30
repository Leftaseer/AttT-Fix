/* 0x5077D0: a constructor: vftable 0x006138C4, +4 and +8 cleared; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006138C4[];

DECOMP(005077D0)
void *__thiscall f_005077D0(void *self)
{
    char *this = (char *)self;
    *(void **)this = d_006138C4;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    return this;
}
