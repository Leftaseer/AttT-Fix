/* 0x4757B0: clears +4 and +8; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004757B0)
void *__thiscall f_004757B0(void *self)
{
    char *this = (char *)self;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    return this;
}
