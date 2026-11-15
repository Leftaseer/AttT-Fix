/* 0x00427520: stores this and the value as a two-dword pair at +0/+4. */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00427520)
void __thiscall f_00427520(void *this, unsigned int *pair, unsigned int value)
{
    pair[0] = (unsigned int)this;
    pair[1] = value;
}
