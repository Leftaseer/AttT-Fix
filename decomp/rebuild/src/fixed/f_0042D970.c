/* 0x0042D970: clears the +0x24 flag. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042D970)
void __thiscall f_0042D970(char *this)
{
    *(unsigned char *)(this + 0x24) = 0;
}
