/* 0x476070: a constructor: vftable 0x0060EA18, +4 and +8 cleared; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060EA18[];

DECOMP(00476070)
void *__thiscall f_00476070(void *self)
{
    char *this = (char *)self;
    *(void **)this = d_0060EA18;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    return this;
}
