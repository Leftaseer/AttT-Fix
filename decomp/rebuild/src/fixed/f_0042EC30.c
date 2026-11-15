/* 0x0042EC30: releases the CConfig singleton (0x006C884C) through slot 0 with 1 and clears the pointer */
/* @func 0042EC30 */
#include "auto_pre.h"
typedef void (__thiscall *release_42EC30)(void *self, int flag);
DECOMP_C void *d_006C884C;                                             /* CConfig::m_instance */

DECOMP(0042EC30)
void __stdcall f_0042EC30(void)
{
    void *o = d_006C884C;
    if (o) {
        ((release_42EC30)(*(void ***)o)[0])(o, 1);
        d_006C884C = 0;
    }
}
