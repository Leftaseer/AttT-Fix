/* 0x0042E3F0: fills count dwords with *src (re-read each turn) and returns the end of dst (a std::vector fill) */
/* @func 0042E3F0 */
#include "auto_pre.h"

DECOMP(0042E3F0)
unsigned int *__stdcall f_0042E3F0(unsigned int *dst, unsigned int count, const unsigned int *src)
{
    while (count--)
        *dst++ = *src;
    return dst;
}
