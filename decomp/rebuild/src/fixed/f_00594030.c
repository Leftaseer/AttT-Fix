/* 0x00594030: the two ARGB colours (+0x24 and +0x4C) as floats 0..1 (times the double at 0x60B368): R, G, B, A at
 * +0x34..+0x40 and +0x5C..+0x68 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_0060B368[];

DECOMP(00594030)
void __thiscall f_00594030(void *this)
{
    char *s = (char *)this;
    double k = *(double *)d_0060B368;
    unsigned int c = *(unsigned int *)(s + 0x24);
    *(float *)(s + 0x34) = (float)((int)(c >> 16 & 0xff) * k);
    *(float *)(s + 0x38) = (float)((int)(c >> 8 & 0xff) * k);
    *(float *)(s + 0x3c) = (float)((int)(c & 0xff) * k);
    *(float *)(s + 0x40) = (float)((int)(c >> 24) * k);
    c = *(unsigned int *)(s + 0x4c);
    *(float *)(s + 0x5c) = (float)((int)(c >> 16 & 0xff) * k);
    *(float *)(s + 0x60) = (float)((int)(c >> 8 & 0xff) * k);
    *(float *)(s + 0x64) = (float)((int)(c & 0xff) * k);
    *(float *)(s + 0x68) = (float)((int)(c >> 24) * k);
}
