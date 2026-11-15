/* 0x00420700: allocates a 0x254-byte object with operator new and constructs it from this: the floats at +0, +4
 * and +0x28, the argument, the block at +0xC, the byte at +8, 2, the block at +0x2C and 1.0f, then two zeroes.
 * Returns the new object, or null when the allocation failed. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size); /* operator new */
DECOMP_C void *__thiscall sub_004B0290(void *self, float f0, float f4, float f28, void *arg, void *block,
                                       unsigned int flag, int two, void *block2, float one, int zero1, int zero2);

DECOMP(00420700)
void *__thiscall f_00420700(void *self, void *arg)
{
    char *s = (char *)self;
    void *object = sub_005E3EAE(0x254);
    if (!object)
        return 0;
    return sub_004B0290(object, *(float *)s, *(float *)(s + 4), *(float *)(s + 0x28), arg, s + 0xc,
                        *(unsigned char *)(s + 8), 2, s + 0x2c, 1.0f, 0, 0);
}
