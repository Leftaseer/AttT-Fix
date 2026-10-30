/* 0x54B8A0: a typed delegate's value copy (out, src): three dwords (a vector: 0x00551F60 reads it through EAX); returns out as the original leaves it in EAX
 * (callers through the delegate may use it; the generated void version left it only by chance) */
/* @conv - 8 */
#include "auto_pre.h"

DECOMP(0054B8A0)
void *__stdcall f_0054B8A0(void *out, void *src)
{
    unsigned int *o = (unsigned int *)out, *s = (unsigned int *)src;
    o[0] = s[0];
    o[1] = s[1];
    o[2] = s[2];
    return out;
}
