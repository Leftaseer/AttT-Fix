/* 0x00428930: builds a sound entry from the key at arg 1 and the record at arg 2 (its first three dwords, the byte
 * at +0xC and its vector at +0x10 copied into +4..+0x14); the object is returned. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004284A0(void *self, char *src);

DECOMP(00428930)
void *__thiscall f_00428930(void *this, unsigned int *key, char *src)
{
    char *s = (char *)this;

    *(unsigned int *)s = *key;
    *(unsigned int *)(s + 4) = *(unsigned int *)src;
    *(float *)(s + 8) = *(float *)(src + 4);
    *(unsigned int *)(s + 0xc) = *(unsigned int *)(src + 8);
    *(unsigned char *)(s + 0x10) = *(unsigned char *)(src + 0xc);
    sub_004284A0(s + 0x14, src + 0x10);
    return s;
}
