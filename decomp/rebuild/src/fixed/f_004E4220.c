/* 0x004E4220: CTimer::Wait: the time since the last call: the performance counter (+0x18) minus the last one (+8),
 * times the period (+0, seconds per tick), a float, capped (0x60A1F8: above it the value at 0x607D54) at +0x14;
 * keeps the counter as the last; returns the time */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060A1F8[], d_00607D54[];
DECOMP_C int (__stdcall *imp_006070A8)(void *) __asm__("__imp__QueryPerformanceCounter@4");

DECOMP(004E4220)
float __thiscall f_004E4220(void *this)
{
    char *s = (char *)this;
    long long now;
    float dt;
    imp_006070A8(s + 0x18);
    now = *(long long *)(s + 0x18);
    /* (the 64-bit difference loaded whole into the x87 and multiplied by the float, rounded once to a float) */
    dt = (float)((double)(now - *(long long *)(s + 8)) * *(float *)s);
    *(float *)(s + 0x14) = dt;
    if (dt > *(float *)d_0060A1F8)
        *(float *)(s + 0x14) = *(float *)d_00607D54;
    *(long long *)(s + 8) = now;
    return *(float *)(s + 0x14);
}
