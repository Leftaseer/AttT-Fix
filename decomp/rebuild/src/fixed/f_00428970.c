/* 0x00428970: builds a sound map node: arg 1..3 for +0, the record of arg 4 (its four dwords, the float +0x10 and
 * the vector at +0x14 copied into +0xC..+0x20), arg 5 as the byte +0x30 and the nil flag +0x31 cleared; the
 * object is returned. */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004284A0(void *self, char *src);

DECOMP(00428970)
void *__thiscall f_00428970(void *this, unsigned int a, unsigned int b, unsigned int c, char *rec, unsigned char flag)
{
    char *s = (char *)this;

    *(unsigned int *)s = a;
    *(unsigned int *)(s + 4) = b;
    *(unsigned int *)(s + 8) = c;
    *(unsigned int *)(s + 0xc) = *(unsigned int *)rec;
    *(unsigned int *)(s + 0x10) = *(unsigned int *)(rec + 4);
    *(float *)(s + 0x14) = *(float *)(rec + 8);
    *(unsigned int *)(s + 0x18) = *(unsigned int *)(rec + 0xc);
    *(unsigned char *)(s + 0x1c) = *(unsigned char *)(rec + 0x10);
    sub_004284A0(s + 0x20, rec + 0x14);
    *(unsigned char *)(s + 0x30) = flag;
    *(unsigned char *)(s + 0x31) = 0;
    return s;
}
