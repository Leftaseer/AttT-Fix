/* 0x0042B0A0: restarts the loop at the first key: the current index and the driven object's index go back to
 * +0x1D0 and the two flags are cleared.  The first index is returned with its low byte zeroed, as the original's
 * `xor al, al` leaves it. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042B0A0)
unsigned int __thiscall f_0042B0A0(char *this)
{
    unsigned int first = *(unsigned int *)(this + 0x1d0);
    *(unsigned int *)(this + 0x1cc) = first;
    *(unsigned int *)(*(char **)(this + 0x1c4) + 0x1d8) = first;
    this[0x20c] = 0;
    this[0x1dc] = 0;
    return first & 0xffffff00;
}
