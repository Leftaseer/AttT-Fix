/* 0x0042ECE0: the singleton pointer held at 0x006C88BC */
/* @func 0042ECE0 */
#include "auto_pre.h"
DECOMP_C void *d_006C88BC;

DECOMP(0042ECE0)
unsigned int __stdcall f_0042ECE0(void)
{
    return (unsigned int)d_006C88BC;
}
