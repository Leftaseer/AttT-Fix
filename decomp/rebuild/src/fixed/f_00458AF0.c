/* 0x458AF0: a bitmap reader's constructor (vftable 0x0060B6A4): its fields cleared; returns this (EAX: callers through a pointer to it may use it, the generated void version
 * left it there only by chance) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060B6A4[];

DECOMP(00458AF0)
void *__thiscall f_00458AF0(void *self)
{
    char *this = (char *)self;
    *(unsigned int *)(this + 4) = 0;
    *(void **)this = d_0060B6A4;
    *(unsigned short *)(this + 0x14) = 0;
    this[0x16] = 0;
    *(unsigned int *)(this + 0x18) = 0;
    *(unsigned int *)(this + 0x1c) = 0;
    *(unsigned int *)(this + 0x10) = 0;
    *(unsigned int *)(this + 0xc) = 0;
    return this;
}
