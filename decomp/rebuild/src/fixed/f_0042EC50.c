/* 0x0042EC50: releases the CConsole singleton (0x006C88B0) through slot 0 with 1 and clears the pointer */
/* @func 0042EC50 */
#include "auto_pre.h"
typedef void (__thiscall *release_42EC50)(void *self, int flag);
DECOMP_C void *d_006C88B0;                                             /* CConsole::m_instance */

DECOMP(0042EC50)
void __stdcall f_0042EC50(void)
{
    void *o = d_006C88B0;
    if (o) {
        ((release_42EC50)(*(void ***)o)[0])(o, 1);
        d_006C88B0 = 0;
    }
}
