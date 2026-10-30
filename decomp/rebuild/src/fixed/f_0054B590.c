/* 0x54B590: a typed delegate's value copy (out, src): the absolute value of a float times 0x00609608 and 0x0068AE10 (doubles); returns src as the original leaves it in EAX
 * (callers through the delegate may use it; the generated void version left it only by chance) */
/* @conv - 8 */
#include "auto_pre.h"
DECOMP_C char d_00609608[];
DECOMP_C char d_0068AE10[];

DECOMP(0054B590)
void *__stdcall f_0054B590(void *out, void *src)
{
    float v = __builtin_fabsf(*(float *)src);
    *(float *)out = (float)((long double)v * *(double *)d_00609608 * *(double *)d_0068AE10);
    return src;
}
