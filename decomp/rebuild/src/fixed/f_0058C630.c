/* 0x0058C630: ChooseHero::vf48: 0x004AC890, then for the hero chosen (+0x1C4 while choosing, +0x1CC set and +0x8C
 * clear; else +0x1C8) the model's vf28(+0x1D4) and 0x0058C3C0(+0x1D0) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C unsigned int __thiscall sub_0058C3C0(void *self, unsigned int a);
typedef void (__thiscall *vf28_58C630)(void *self, unsigned int a);

DECOMP(0058C630)
unsigned int __thiscall f_0058C630(void *this)
{
    char *s = (char *)this;
    void **m;
    sub_004AC890(this);
    if (s[0x1cc] && !s[0x8c]) {
        m = *(void ***)(s + 0x1c4);
        ((vf28_58C630)(*(void ***)m)[0x28 / 4])(m, *(unsigned int *)(s + 0x1d4));
        return sub_0058C3C0(*(void **)(s + 0x1c4), *(unsigned int *)(s + 0x1d0));
    }
    m = *(void ***)(s + 0x1c8);
    ((vf28_58C630)(*(void ***)m)[0x28 / 4])(m, *(unsigned int *)(s + 0x1d4));
    return sub_0058C3C0(*(void **)(s + 0x1c8), *(unsigned int *)(s + 0x1d0));
}
