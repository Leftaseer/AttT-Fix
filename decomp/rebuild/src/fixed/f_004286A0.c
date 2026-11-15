/* 0x004286A0: copies a sound entry (the key, float at +4, count at +8 and the byte +0xC) and copy-constructs its
 * vector from src+0x10 into +0x10; the object is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004284A0(void *self, char *src);

DECOMP(004286A0)
void *__thiscall f_004286A0(void *this, char *src)
{
    char *s = (char *)this;

    *(unsigned int *)s = *(unsigned int *)src;
    *(float *)(s + 4) = *(float *)(src + 4);
    *(unsigned int *)(s + 8) = *(unsigned int *)(src + 8);
    *(unsigned char *)(s + 0xc) = *(unsigned char *)(src + 0xc);
    sub_004284A0(s + 0x10, src + 0x10);
    return s;
}
