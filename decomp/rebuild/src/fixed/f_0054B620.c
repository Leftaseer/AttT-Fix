/* 0x54B620: a typed delegate's value copy (out, src): the absolute value of a float; returns src as the original leaves it in EAX
 * (callers through the delegate may use it; the generated void version left it only by chance) */
/* @conv - 8 */
#include "auto_pre.h"

DECOMP(0054B620)
void *__stdcall f_0054B620(void *out, void *src)
{
    *(float *)out = __builtin_fabsf(*(float *)src);
    return src;
}
