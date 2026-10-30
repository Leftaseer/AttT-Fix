/* 0x54B7F0: a typed delegate's value copy (out, src): a word; returns src as the original leaves it in EAX
 * (callers through the delegate may use it; the generated void version left it only by chance) */
/* @conv - 8 */
#include "auto_pre.h"

DECOMP(0054B7F0)
void *__stdcall f_0054B7F0(void *out, void *src)
{
    *(unsigned short *)out = *(unsigned short *)src;
    return src;
}
