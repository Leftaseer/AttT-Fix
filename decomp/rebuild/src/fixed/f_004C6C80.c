/* 0x004C6C80: picks the texture of a spellbook page button: +0x98 when highlighted (+0x2E4) unless the selected
 * school (+0x26C == 2) has a spell of level 4..6 (+0x278 by the school) that 0x004C6A90 rates 3; else +0x94; set by
 * vfE8 of the image at +0x84 (a tail call reusing the argument's slot: one argument) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned char __thiscall sub_004C6A90(void *self);
typedef unsigned int (__thiscall *vfE8_4C6C80)(void *self, unsigned int tex);

DECOMP(004C6C80)
unsigned int __thiscall f_004C6C80(void *this, unsigned int unused)
{
    char *s = (char *)this;
    int b = 0;
    void **img;
    if ((unsigned char)(s[0x26c] + 1) == 3) {
        int v = *(int *)(s + *(int *)(s + 0x26c) * 4 + 0x278);
        if ((v < 0 || v > 3) && v >= 4 && v <= 6 && sub_004C6A90(this) == 3)
            b = 1;
    }
    img = *(void ***)(s + 0x84);
    return ((vfE8_4C6C80)(*(void ***)img)[0xe8 / 4])(img, s[0x2e4] && !b ? *(unsigned int *)(s + 0x98)
                                                                          : *(unsigned int *)(s + 0x94));
}
