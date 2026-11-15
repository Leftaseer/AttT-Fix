/* 0x0042ECC0: releases the CEngine singleton (0x006C88B8) through slot 0 with 1 and clears the pointer */
/* @func 0042ECC0 */
#include "auto_pre.h"
typedef void (__thiscall *release_42ECC0)(void *self, int flag);
DECOMP_C void *d_006C88B8;                                             /* CEngine::m_instance */

DECOMP(0042ECC0)
void __stdcall f_0042ECC0(void)
{
    void *o = d_006C88B8;
    if (o) {
        ((release_42ECC0)(*(void ***)o)[0])(o, 1);
        d_006C88B8 = 0;
    }
}
