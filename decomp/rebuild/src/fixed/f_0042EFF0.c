/* 0x0042EFF0: releases CEngine, CConfig and the unnamed 0x006C88B4 singleton, clearing the paired globals */
/* @func 0042EFF0 */
#include "auto_pre.h"
typedef void (__thiscall *release_42EFF0)(void *self, int flag);
DECOMP_C void *d_006C88B8;                                             /* CEngine::m_instance */
DECOMP_C void *d_006C88A8;
DECOMP_C void *d_006C884C;                                             /* CConfig::m_instance */
DECOMP_C void *d_006C88A4;
DECOMP_C void *d_006C88B4;

DECOMP(0042EFF0)
void __stdcall f_0042EFF0(void)
{
    void *o;
    d_006C88A8 = 0;
    o = d_006C88B8;
    if (o) {
        ((release_42EFF0)(*(void ***)o)[0])(o, 1);
        d_006C88B8 = 0;
    }
    d_006C88A4 = 0;
    o = d_006C884C;
    if (o) {
        ((release_42EFF0)(*(void ***)o)[0])(o, 1);
        d_006C884C = 0;
    }
    o = d_006C88B4;
    if (o) {
        ((release_42EFF0)(*(void ***)o)[0])(o, 1);
        d_006C88B4 = 0;
    }
}
