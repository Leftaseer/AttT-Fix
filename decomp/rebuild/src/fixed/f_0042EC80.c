/* 0x0042EC80: releases the singleton at 0x006C88B4 through slot 0 with 1 and clears the pointer */
/* @func 0042EC80 */
#include "auto_pre.h"
typedef void (__thiscall *release_42EC80)(void *self, int flag);
DECOMP_C void *d_006C88B4;

DECOMP(0042EC80)
void __stdcall f_0042EC80(void)
{
    void *o = d_006C88B4;
    if (o) {
        ((release_42EC80)(*(void ***)o)[0])(o, 1);
        d_006C88B4 = 0;
    }
}
