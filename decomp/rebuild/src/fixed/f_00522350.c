/* 0x00522350: places the object at the current one of its positions (+0x244, eight bytes each, the index at +0x264:
 * vf6C) and its two groups of attached objects (12-byte entries: the object and its offset; +0x280/+0x284 and
 * +0x274/+0x278) at that position plus their offsets */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef void (__thiscall *vf6C_522350)(void *self, float *pos);

DECOMP(00522350)
void __thiscall f_00522350(void *this)
{
    char *s = (char *)this;
    float *pos = (float *)(s + *(int *)(s + 0x264) * 8 + 0x244);
    unsigned int i;
    ((vf6C_522350)(*(void ***)this)[0x6c / 4])(this, pos);
    for (i = 0; i < *(unsigned int *)(s + 0x284); i++) {
        float *e = (float *)(*(char **)(s + 0x280) + i * 0xc);
        void **o = *(void ***)e;
        float p[2];
        p[1] = e[2] + pos[1];
        p[0] = pos[0] + e[1];
        ((vf6C_522350)(*(void ***)o)[0x6c / 4])(o, p);
    }
    for (i = 0; i < *(unsigned int *)(s + 0x278); i++) {
        float *e = (float *)(*(char **)(s + 0x274) + i * 0xc);
        void **o = *(void ***)e;
        float p[2];
        p[1] = e[2] + pos[1];
        p[0] = e[1] + pos[0];
        ((vf6C_522350)(*(void ***)o)[0x6c / 4])(o, p);
    }
}
