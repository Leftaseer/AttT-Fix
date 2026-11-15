/* 0x0042AED0: CInvSimpleAnimation's virtual: the object's slot 0x30 with a zero argument, its result returned. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042AED0)
unsigned int __thiscall f_0042AED0(void *this)
{
    return ((unsigned int (__thiscall *)(void *, unsigned int))(*(void ***)this)[0x30])(this, 0);
}
