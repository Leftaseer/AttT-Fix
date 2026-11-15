/* CSimpleAnimation 0x0042A6A0: restarts the playback at the first key (+0x1D0 goes to the current index +0x1CC and
 * to the driven object's index at +0x1D8, the "stopped at the end" flag +0x1DC is cleared); the index is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042A6A0)
unsigned int __thiscall f_0042A6A0(char *this)
{
    unsigned int first = *(unsigned int *)(this + 0x1d0);
    char *driven = *(char **)(this + 0x1c4);

    *(unsigned int *)(this + 0x1cc) = first;
    *(unsigned int *)(driven + 0x1d8) = first;
    this[0x1dc] = 0;
    return first;
}
