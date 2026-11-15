/* 0x0042B160: advances the loop's current key by one.  +0x20C picks the direction: forwards the index runs from
 * +0x204 up to the end key (+0x208) and then wraps to +0x208+1, backwards it runs down from +0x208+1 to +0x204.
 * Past the last key (+0x1D4) backwards it stops there and sets the stop flag.  The driven object follows the index;
 * a stopped loop returns EAX untouched. */
/* @conv EAX,ECX 0 */
/* @func 0042B160 custom */
#include "auto_pre.h"

DECOMP(0042B160)
unsigned int __cdecl f_0042B160(unsigned int in_eax, char *this)
{
    unsigned int index;

    if (this[0x1dc])
        return in_eax;
    index = ++*(unsigned int *)(this + 0x1cc);
    if (this[0x20c]) {
        if (index == *(unsigned int *)(this + 0x204)) {
            *(unsigned int *)(this + 0x1cc) = *(unsigned int *)(this + 0x208) + 1;
        } else if (index > *(unsigned int *)(this + 0x1d4)) {
            *(unsigned int *)(this + 0x1cc) = *(unsigned int *)(this + 0x1d4);
            this[0x1dc] = 1;
            *(unsigned int *)(*(char **)(this + 0x1c4) + 0x1d8) = *(unsigned int *)(this + 0x1cc);
            return *(unsigned int *)(this + 0x1cc);
        }
    } else if (index == *(unsigned int *)(this + 0x208) + 1) {
        *(unsigned int *)(this + 0x1cc) = *(unsigned int *)(this + 0x204);
    }
    *(unsigned int *)(*(char **)(this + 0x1c4) + 0x1d8) = *(unsigned int *)(this + 0x1cc);
    return *(unsigned int *)(this + 0x1cc);
}
