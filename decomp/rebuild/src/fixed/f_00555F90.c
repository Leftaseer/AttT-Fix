/* 0x555F90: the member at +0xC constructed (vftable 0x0060B238, +0x10 and +0x14 cleared); returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060B238[];

DECOMP(00555F90)
void *__thiscall f_00555F90(void *self)
{
    char *this = (char *)self;
    *(void **)(this + 0xc) = d_0060B238;
    *(unsigned int *)(this + 0x10) = 0;
    *(unsigned int *)(this + 0x14) = 0;
    return this;
}
