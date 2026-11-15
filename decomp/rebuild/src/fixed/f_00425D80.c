/* 0x00425D80: the small ActionScript base's destructor part: the vtable 0x00607E94, one less registry user
 * (0x006C8738) and the CGameObject base destructor (0x00424C70, a tail call) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607E94[];
DECOMP_C int d_006C8738;
DECOMP_C void __thiscall sub_00424C70(void *self);

DECOMP(00425D80)
void __thiscall f_00425D80(void *this)
{
    *(const void **)this = d_00607E94;
    d_006C8738--;
    sub_00424C70(this);
}
