/* 0x00426A00: the alpha button's control constructor: the 3D control with arg 1, the 2D mesh part (+0x54) with
 * arg 3, the vtables 0x00608188 and 0x0060809C, then a 0x54-byte texture built from arg 2 (flag 1) at +0x98. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_00608188[], d_0060809C[];
DECOMP_C void __thiscall sub_004428F0(void *self, void *arg);
DECOMP_C void __thiscall sub_00479B30(void *self, void *arg);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_004DF920(void *texture, void *arg, int flag);
DECOMP_C void __thiscall sub_00479870(void *self);

DECOMP(00426A00)
void *__thiscall f_00426A00(void *this, void *a, void *b, void *c)
{
    char *s = (char *)this;
    void *texture;
    sub_004428F0(s, a);
    sub_00479B30(s + 0x54, c);
    *(const void **)s = d_00608188;
    *(const void **)(s + 0x54) = d_0060809C;
    texture = sub_005E3EAE(0x54);
    *(void **)(s + 0x98) = texture ? sub_004DF920(texture, b, 1) : 0;
    s[0x9c] = 1;
    sub_00479870(s + 0x54);
    return s;
}
