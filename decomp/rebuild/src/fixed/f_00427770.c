/* 0x00427770: copies 12-byte elements from [first, last) to dest (skipping the copy for a null dest); returns the
 * advanced dest. */
/* @conv 0 */
#include "auto_pre.h"

DECOMP(00427770)
void *__cdecl f_00427770(void *first, void *last, void *dest)
{
    char *src = (char *)first, *out = (char *)dest;
    while (src != (char *)last) {
        if (out) {
            ((unsigned int *)out)[0] = ((unsigned int *)src)[0];
            ((unsigned int *)out)[1] = ((unsigned int *)src)[1];
            ((unsigned int *)out)[2] = ((unsigned int *)src)[2];
        }
        src += 0xc;
        out += 0xc;
    }
    return out;
}
