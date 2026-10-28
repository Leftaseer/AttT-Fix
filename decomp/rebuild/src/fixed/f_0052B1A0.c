/* 0x0052B1A0: x to the integer power n, by squaring (1/x^-n for a negative n) */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP(0052B1A0)
double __cdecl f_0052B1A0(double x, int n)
{
    unsigned int u = n < 0 ? -(unsigned int)n : (unsigned int)n;
    double r = 1.0;
    for (;;) {
        if (u & 1)
            r *= x;
        u >>= 1;
        if (u == 0)
            break;
        x *= x;
    }
    return n < 0 ? 1.0 / r : r;
}
