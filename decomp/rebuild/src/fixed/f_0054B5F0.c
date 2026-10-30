/* 0x54B5F0: a typed delegate's value copy (out, src): four dwords; returns the last dword as the original leaves it in EAX
 * (callers through the delegate may use it; the generated void version left it only by chance) */
/* @conv - 8 */
#include "auto_pre.h"

DECOMP(0054B5F0)
unsigned int __stdcall f_0054B5F0(void *out, void *src)
{
    unsigned int *o = (unsigned int *)out, *s = (unsigned int *)src;
    o[0] = s[0];
    o[1] = s[1];
    o[2] = s[2];
    o[3] = s[3];
    return s[3];
}
