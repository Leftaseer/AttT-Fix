/* 0x0042A7A0: steps the playing animation one key forward (unless it is stopped at the end, +0x1DC, or the object
 * is hidden, +0x49) and clamps the index to the last key, where the stop flag is set; the object at +0x1C4 follows.
 * The input EAX passes through when nothing is stepped and the object pointer is returned otherwise. */
/* @conv ECX,EAX 0 */
/* @func 0042A7A0 custom */
#include "auto_pre.h"

DECOMP(0042A7A0)
unsigned int __cdecl f_0042A7A0(char *this, unsigned int in_eax)
{
    char *driven;
    unsigned int limit;

    if (!this[0x1dc] && this[0x49]) {
        *(unsigned int *)(this + 0x1cc) += 1;
        limit = *(unsigned int *)(this + 0x1d4);
        if (*(unsigned int *)(this + 0x1cc) > limit) {
            *(unsigned int *)(this + 0x1cc) = limit;
            this[0x1dc] = 1;
        }
        driven = *(char **)(this + 0x1c4);
        *(unsigned int *)(driven + 0x1d8) = *(unsigned int *)(this + 0x1cc);
        return (unsigned int)driven;
    }
    return in_eax;
}
