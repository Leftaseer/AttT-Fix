/* 0x55BA60: a forest group's constructor (vftable 0x0061BF98, +0x1BC placements cleared); returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0061BF98[];

DECOMP(0055BA60)
void *__thiscall f_0055BA60(void *self)
{
    char *this = (char *)self;
    *(void **)this = d_0061BF98;
    *(unsigned int *)(this + 0x1bc) = 0;
    return this;
}
