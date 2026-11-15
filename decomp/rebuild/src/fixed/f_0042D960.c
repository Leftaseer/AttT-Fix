/* 0x0042D960: sets the +0x24 flag. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042D960)
void __thiscall f_0042D960(char *this)
{
    *(unsigned char *)(this + 0x24) = 1;
}
