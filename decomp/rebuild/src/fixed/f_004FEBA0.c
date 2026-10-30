/* 0x4FEBA0: clears +4; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004FEBA0)
void *__thiscall f_004FEBA0(void *self)
{
    char *this = (char *)self;
    *(unsigned int *)(this + 4) = 0;
    return this;
}
