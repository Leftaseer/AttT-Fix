/* 0x0042BC90: picks the texture for the item p: +0x94 when its kind (p+0x50) is 11 or more or allowed for the hero's
 * class (the bit of the kind in the word table 0x6BF684 by the class at +0x1D8 of 0x00425F60's hero), else +0x98,
 * set by vfE8 of the image at +0x8C (a tail call reusing the argument's slot: one argument) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C char d_006BF684[];
typedef unsigned int (__thiscall *vfE8_42BC90)(void *self, unsigned int tex);

DECOMP(0042BC90)
unsigned int __thiscall f_0042BC90(void *this, char *p)
{
    char *s = (char *)this;
    unsigned int kind = *(unsigned int *)(p + 0x50);
    unsigned int tex;
    void **img;
    if (kind >= 0xb)
        tex = *(unsigned int *)(s + 0x94);
    else {
        unsigned short bits = ((unsigned short *)d_006BF684)[*(int *)(sub_00425F60() + 0x1d8)];
        tex = (1u << kind) & bits ? *(unsigned int *)(s + 0x94) : *(unsigned int *)(s + 0x98);
    }
    img = *(void ***)(s + 0x8c);
    return ((vfE8_42BC90)(*(void ***)img)[0xe8 / 4])(img, tex);
}
