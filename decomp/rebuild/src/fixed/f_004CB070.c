/* 0x004CB070: an NPC's walk to a target (the unit pointer at +8, the target at +0xC): while walking (+0x20) and the
 * unit has arrived (+0x1DC) it takes the target and vfD8, then 0x004CAF00; otherwise when the unit is free (vfE4) and
 * the target's name (+8) differs from the unit's it starts walking (vfDC), else 0x004CAF00 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004CAF00(void *self);
DECOMP_C int (__cdecl *imp_00607368)(const void *, const void *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@0@Z");
typedef char (__thiscall *vf_4CB070)(void *self);

#define UNIT (**(char ***)(s + 8))

DECOMP(004CB070)
void __thiscall f_004CB070(void *this)
{
    char *s = (char *)this;
    if (s[0x20]) {
        if (!UNIT[0x1dc])
            return;
        s[0x20] = 0;
        **(char ***)(s + 8) = *(char **)(s + 0xc);
        ((vf_4CB070)(*(void ***)UNIT)[0xd8 / 4])(UNIT);
    } else {
        if (!((vf_4CB070)(*(void ***)UNIT)[0xe4 / 4])(UNIT))
            return;
        if ((char)imp_00607368(*(char **)(s + 0xc) + 8, UNIT + 8)) {
            s[0x20] = 1;
            ((vf_4CB070)(*(void ***)UNIT)[0xdc / 4])(UNIT);
            return;
        }
    }
    sub_004CAF00(this);
}
