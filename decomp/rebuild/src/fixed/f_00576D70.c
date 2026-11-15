/* 0x00576D70: builds the object at this from a byte: the original aliases its own stack (the top byte of the
 * saved ECX, `lea [esp+7]` after `push ecx`) and passes that address to 0x576C20 (which does not read it);
 * returns this.  The generated code calls 0x576C20 as cdecl with ECX (the object) and EDX (unread) first. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00576C20(void *self, unsigned int edx_in, void *arg);

DECOMP(00576D70)
void *__thiscall f_00576D70(void *this)
{
    unsigned char high = (unsigned char)((unsigned int)this >> 24);
    sub_00576C20(this, 0, &high);
    return this;
}
