/* 0x0046CEB0: CInput::ResetMouse marks every mouse button released (6) and clears the
 * three click flags at +0x7C4..+0x7C6. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0046CEB0)
void __thiscall f_0046CEB0(char *this)
{
    unsigned int i;

    for (i = 0; i < *(unsigned int *)(this + 0x670); i++)
        *(unsigned int *)(*(char **)(this + 0x66c) + i * 4) = 6;
    this[0x7c5] = 0;
    this[0x7c4] = 0;
    this[0x7c6] = 0;
}
