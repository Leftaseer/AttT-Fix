/* 0x4C1C00: clears +0; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004C1C00)
void *__thiscall f_004C1C00(void *self)
{
    char *this = (char *)self;
    *(unsigned int *)this = 0;
    return this;
}
