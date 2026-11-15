/* 0x0042B680: releases the scene's six object slots +0xC4, +0xC0, +0xBC, +0xB8, +0xCC, +0xC8 (each through the
 * first vtable entry with 1 as the deleting flag, then the slot is cleared) and returns the value at +0x3C. */
/* @conv ECX 0 */
#include "auto_pre.h"

typedef void (__thiscall *vf0_42B680)(void *self, int freeing);

#define VT(o) (*(void ***)(o))

static void release_42B680(char *s, unsigned int offset)
{
    void *object = *(void **)(s + offset);
    if (object) {
        ((vf0_42B680)VT(object)[0])(object, 1);
        *(void **)(s + offset) = 0;
    }
}

DECOMP(0042B680)
void *__thiscall f_0042B680(char *this)
{
    release_42B680(this, 0xc4);
    release_42B680(this, 0xc0);
    release_42B680(this, 0xbc);
    release_42B680(this, 0xb8);
    release_42B680(this, 0xcc);
    release_42B680(this, 0xc8);
    return *(void **)(this + 0x3c);
}
