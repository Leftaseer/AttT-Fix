/* 0x4D4350: advances +0 by 6; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004D4350)
void *__thiscall f_004D4350(void *self)
{
    char *this = (char *)self;
    *(int *)this += 6;
    return this;
}
