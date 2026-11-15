/* 0x0042EB50: GetKeyState(VK_CONTROL), then GetKeyState(VK_HOME) when control is down (the results are otherwise
 * unused) */
/* @func 0042EB50 */
#include "auto_pre.h"
DECOMP_C short (__stdcall *imp_006076D0)(int key) __asm__("__imp__GetKeyState");

DECOMP(0042EB50)
void __stdcall f_0042EB50(void)
{
    if (imp_006076D0(0x11) < 0)
        imp_006076D0(0x24);
}
