/* 0x0059D8D0: while running (first byte), adds a tenth of the 64-bit count at 8 to the 64-bit total at 0x10 */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0059D8D0)
void __thiscall f_0059D8D0(char *this)
{
    if (*this != 0)
        *(long long *)(this + 0x10) += *(long long *)(this + 8) / 10;
}
