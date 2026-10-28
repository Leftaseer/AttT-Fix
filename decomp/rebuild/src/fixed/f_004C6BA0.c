/* 0x004C6BA0: CSpellBookScene::vf6: with no page open (+0x274) the scene's update (0x004B1E20) and vf08 of +0x78;
 * a page that says it is done (vf60) only the update; otherwise the page's vf50, the update, the page's vf4C and
 * vf08, then vf08 of +0x78; returns what the last call returned */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_004B1E20(void *self);
typedef unsigned int (__thiscall *vf_4C6BA0)(void *self);

#define VCALL(o, off) ((vf_4C6BA0)(*(void ***)(o))[(off) / 4])(o)

DECOMP(004C6BA0)
unsigned int __thiscall f_004C6BA0(void *this)
{
    char *s = (char *)this;
    if (!*(void **)(s + 0x274)) {
        sub_004B1E20(this);
        return VCALL(*(void **)(s + 0x78), 8);
    }
    if ((char)VCALL(*(void **)(s + 0x274), 0x60))
        return sub_004B1E20(this);
    VCALL(*(void **)(s + 0x274), 0x50);
    sub_004B1E20(this);
    VCALL(*(void **)(s + 0x274), 0x4c);
    VCALL(*(void **)(s + 0x274), 8);
    return VCALL(*(void **)(s + 0x78), 8);
}
