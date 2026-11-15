/* 0x0042D910: clears the +0x24C byte. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042D910)
void __thiscall f_0042D910(char *this)
{
    *(unsigned char *)(this + 0x24c) = 0;
}
