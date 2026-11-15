/* 0x0042AE80: a constructor that only returns the object passed in EAX (and pops its three stack arguments). */
/* @conv EAX 12 */
/* @func 0042AE80 custom */
#include "auto_pre.h"

DECOMP(0042AE80)
void *__cdecl f_0042AE80(void *self)
{
    return self;
}
