/* 0x00425F30: stores the vtable 0x00607ED0 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607ED0[];

DECOMP(00425F30)
void __thiscall f_00425F30(void *this)
{
    *(const void **)this = d_00607ED0;
}
