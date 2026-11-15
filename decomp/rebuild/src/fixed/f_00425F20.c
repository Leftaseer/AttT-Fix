/* 0x00425F20: stores the vtable 0x00607ED0 and returns this */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607ED0[];

DECOMP(00425F20)
void *__thiscall f_00425F20(void *this)
{
    *(const void **)this = d_00607ED0;
    return this;
}
