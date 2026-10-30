/* 0x4FEC90: a constructor: vftable 0x00613600, +4 and +8 cleared; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00613600[];

DECOMP(004FEC90)
void *__thiscall f_004FEC90(void *self)
{
    char *this = (char *)self;
    *(void **)this = d_00613600;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    return this;
}
