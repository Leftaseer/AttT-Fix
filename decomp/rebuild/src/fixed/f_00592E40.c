/* 0x00592E40: releases the captured control (virtual function 0x24 of the object at 0x8D1244, then cleared)
 * and the mouse capture (ReleaseCapture, which the original tail-jumps to) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
DECOMP_C char d_008D1244[];

DECOMP(00592E40)
int __stdcall f_00592E40(void)
{
    void *c = *(void **)d_008D1244;
    if (c != 0) {
        ((void (__thiscall *)(void *))(*(void ***)c)[0x24 / 4])(c);
        *(void **)d_008D1244 = 0;
    }
    return imp_00607648();
}
