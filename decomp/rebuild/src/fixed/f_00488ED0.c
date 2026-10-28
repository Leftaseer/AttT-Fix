/* 0x00488ED0: ends the current profiler section (0x6CA274): the time since its start (+0x20, performance counter
 * ticks times the period at 0x6CA5A0) at +0x2C, added to the total (+0), the longest (+4) and shortest (+8) kept,
 * the 64-bit call count (+0x30) incremented; the parent (+0x38) becomes current */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C char d_006CA274[], d_006CA5A0[];
DECOMP_C int (__stdcall *imp_006070A8)(void *) __asm__("__imp__QueryPerformanceCounter@4");

#define CUR (*(char **)d_006CA274)

DECOMP(00488ED0)
void __cdecl f_00488ED0(void)
{
    char *n = CUR;
    long long t;
    float dt;
    imp_006070A8(&t);
    *(float *)(n + 0x2c) = (float)((double)(t - *(long long *)(n + 0x20)) * *(float *)d_006CA5A0);
    *(long long *)(n + 0x20) = t;
    dt = *(float *)(n + 0x2c);
    n = CUR;
    *(float *)n = dt + *(float *)n;
    n = CUR;
    if (!*(long long *)(n + 0x30)) {
        *(float *)(n + 8) = dt;
        *(float *)(CUR + 4) = dt;
    } else {
        if (dt > *(float *)(n + 4)) {
            *(float *)(n + 4) = dt;
            n = CUR;
        }
        if (*(float *)(n + 8) > dt)
            *(float *)(n + 8) = dt;
    }
    ++*(long long *)(n + 0x30);
    CUR = *(char **)(CUR + 0x38);
}
