/* 0x004B1E20: CScene::vf6: with an active dialog (+0x44) that is modal (vf1C) both layers (+4, +0x54) get
 * 0x004B1BC0(false) and the dialog's vf18 (its result returned); otherwise vf08 of every object in the lists at +0x10
 * and +0x60 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B1BC0(void *layer, unsigned int flag);
typedef unsigned int (__thiscall *vf_4B1E20)(void *self);

DECOMP(004B1E20)
unsigned int __thiscall f_004B1E20(void *this)
{
    char *s = (char *)this;
    void **d = *(void ***)(s + 0x44), **node;
    if (d && (char)((vf_4B1E20)(*(void ***)d)[0x1c / 4])(d)) {
        sub_004B1BC0(s + 4, 0);
        sub_004B1BC0(s + 0x54, 0);
        d = *(void ***)(s + 0x44);
        return ((vf_4B1E20)(*(void ***)d)[0x18 / 4])(d);
    }
    for (node = **(void ****)(s + 0x10); node != *(void ***)(s + 0x10); node = (void **)*node) {
        void **o = (void **)node[2];
        ((vf_4B1E20)(*(void ***)o)[2])(o);
    }
    for (node = **(void ****)(s + 0x60); node != *(void ***)(s + 0x60); node = (void **)*node) {
        void **o = (void **)node[2];
        ((vf_4B1E20)(*(void ***)o)[2])(o);
    }
    return 0;
}
