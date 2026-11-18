/* 0x0046CEF0: CInput::ResetKeys clears the 256-byte key state at +0x48 and the low byte
 * of every key-list entry for the current frame. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E40BE(void *dst, int value, unsigned int size);

DECOMP(0046CEF0)
void __thiscall f_0046CEF0(char *this)
{
    unsigned int i;

    sub_005E40BE(this + 0x48, 0, 0x100);
    for (i = 0; i < *(unsigned int *)(this + 0x664); i++)
        (*(char **)(this + 0x660))[i * 2] = 0;
}
