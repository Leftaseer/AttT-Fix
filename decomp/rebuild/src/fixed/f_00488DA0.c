/* 0x00488DA0: QueryPerformanceCounter delta in 64-bit ticks scaled by the frequency constant into the float
 * at 0x1c, with the new counter value saved at 0x10/0x14.  The original loads the 64-bit difference with
 * fild (exact in x87), multiplies by the float constant and rounds once at the fstp dword; the generated C
 * converted the difference to float first ((float)CONCAT44(...)), which for large deltas changes the result.
 * The subtraction is the original's sub/sbb pair: the counter is compared as 64 bits. */
#include "auto_pre.h"

DECOMP_C int (__stdcall *imp_006070A8)(void *) __asm__("__imp__QueryPerformanceCounter");
DECOMP_C char d_006CA5A0[];

DECOMP(00488DA0)
float __fastcall f_00488DA0(int param_1)
{
    unsigned long long now, prev;
    float out;

    imp_006070A8(&now);
    prev = *(unsigned *)(param_1 + 0x10) | ((unsigned long long)*(unsigned *)(param_1 + 0x14) << 32);
    out = (float)((double)(long long)(now - prev) * (double)*(float *)d_006CA5A0);
    *(unsigned *)(param_1 + 0x10) = (unsigned)now;
    *(unsigned *)(param_1 + 0x14) = (unsigned)(now >> 32);
    *(float *)(param_1 + 0x1c) = out;
    return *(float *)(param_1 + 0x1c);
}
