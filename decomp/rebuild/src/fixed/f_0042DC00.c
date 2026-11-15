/* 0x0042DC00: forwards to the handler at +0x10 with the object at +0x14: handler(object, this, arg); returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042DC00)
void *__thiscall f_0042DC00(char *this, unsigned int arg)
{
    ((void (__thiscall *)(void *, void *, unsigned int))*(void **)(this + 0x10))(*(void **)(this + 0x14), this, arg);
    return this;
}
