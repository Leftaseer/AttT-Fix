/* 0x00426450: the 2D render position +0x58/+0x5C takes the two dwords of the vector and the +0x60 flag sets;
 * returns the second dword */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00426450)
unsigned int __thiscall f_00426450(void *this, unsigned int *v)
{
    char *s = (char *)this;
    *(unsigned int *)(s + 0x58) = v[0];
    *(unsigned int *)(s + 0x5c) = v[1];
    s[0x60] = 1;
    return v[1];
}
