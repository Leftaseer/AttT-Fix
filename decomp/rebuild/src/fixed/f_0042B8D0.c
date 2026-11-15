/* 0x0042B8D0: calls entry `index` of the (function, offset) table 0x006C8858/0x006C885C (8-byte records): the
 * function's `this` is this + the record's offset, its stack argument is `arg`. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_006C8858[], d_006C885C[];

DECOMP(0042B8D0)
void __thiscall f_0042B8D0(char *this, unsigned int index, unsigned int arg)
{
    void (__thiscall *fn)(void *self, unsigned int arg) =
        *(void (__thiscall **)(void *, unsigned int))(d_006C8858 + index * 8);
    int offset = *(int *)(d_006C885C + index * 8);
    fn(this + offset, arg);
}
