/* 0x004285F0: clears the sound entry: the dwords at +0x14..+0x1C, the byte +0xC, the key at +0 and the float +4;
 * the object is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004285F0)
void *__thiscall f_004285F0(void *this)
{
    char *s = (char *)this;

    *(unsigned int *)(s + 0x14) = 0;
    *(unsigned int *)(s + 0x18) = 0;
    *(unsigned int *)(s + 0x1c) = 0;
    *(unsigned char *)(s + 0xc) = 0;
    *(unsigned int *)s = 0;
    *(float *)(s + 4) = 0.0f;
    *(unsigned int *)(s + 8) = 0;
    return s;
}
