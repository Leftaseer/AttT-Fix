/* 0x48CE50: clears +4, +8 and +0xC; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0048CE50)
void *__thiscall f_0048CE50(void *self)
{
    char *this = (char *)self;
    *(unsigned int *)(this + 4) = 0;
    *(unsigned int *)(this + 8) = 0;
    *(unsigned int *)(this + 0xc) = 0;
    return this;
}
