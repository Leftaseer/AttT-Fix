/* 0x00427440: copies a 4-byte value and a byte into the object; returns this. */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00427440)
void *__thiscall f_00427440(void *this, unsigned int *value, unsigned char *byte)
{
    char *s = (char *)this;
    *(unsigned int *)s = *value;
    s[4] = *byte;
    return s;
}
