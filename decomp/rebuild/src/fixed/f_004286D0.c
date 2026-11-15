/* 0x004286D0: copies a sound record (four dwords and the byte +0x10) and copy-constructs its vector from src+0x14
 * into +0x14; the object is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004284A0(void *self, char *src);

DECOMP(004286D0)
void *__thiscall f_004286D0(void *this, char *src)
{
    char *s = (char *)this;

    *(unsigned int *)s = *(unsigned int *)src;
    *(unsigned int *)(s + 4) = *(unsigned int *)(src + 4);
    *(unsigned int *)(s + 8) = *(unsigned int *)(src + 8);
    *(unsigned int *)(s + 0xc) = *(unsigned int *)(src + 0xc);
    *(unsigned char *)(s + 0x10) = *(unsigned char *)(src + 0x10);
    sub_004284A0(s + 0x14, src + 0x14);
    return s;
}
