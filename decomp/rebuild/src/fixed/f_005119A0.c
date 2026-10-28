/* 0x005119A0: new of a 0x58-byte object built by 0x00431C60 (four arguments); NULL when out of memory (the original
 * frees the memory again if the constructor throws, which this C does not) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_00431C60(void *self, float *a, float *b, int c, unsigned int d);

DECOMP(005119A0)
void *__cdecl f_005119A0(float *a, float *b, int c, unsigned int d)
{
    void *p = sub_005E3EAE(0x58);
    if (p)
        return sub_00431C60(p, a, b, c, d);
    return 0;
}
