/* 0x0042D7F0: out = ECX * m (D3DXMatrixMultiply through its thunk 0x5B8020), returns out */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void * __stdcall sub_005B8020(void *out, void *a, void *b);

DECOMP(0042D7F0)
void * __thiscall f_0042D7F0(void *a, void *out, void *b)
{
    sub_005B8020(out, a, b);
    return out;
}
