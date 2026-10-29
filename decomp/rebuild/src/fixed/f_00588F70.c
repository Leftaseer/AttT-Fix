/* 0x00588F70: Lua method Cancel of the conversation (0x006C71B0): +0x338 cleared, 0x00588B30; unless +0x334 is set
 * the table +0x2CC is emptied and the conversation camera (+0x2C8, 0x0058B970) plays Talk. Returns 0 (no
 * results) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00588B30(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0058B970(void *self, void *tbl, void *cam, void *anim);
DECOMP_C char d_00607CC4[], d_0061009C[], d_006120A0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00588F70)
int __thiscall f_00588F70(void *self, void *L)
{
    char *this = (char *)self;
    *(int *)(this + 0x338) = 0;
    sub_00588B30(this);
    if (*(int *)(this + 0x334) == 0) {
        unsigned int t[3], anim[7], cam[7];
        t[1] = 0;
        t[0] = (unsigned int)(size_t)d_00607CC4;
        t[2] = 0xffffffffu;
        sub_0057A860(this + 0x2cc, t);
        sub_004220A0(t);
        imp_00607324(anim, d_0061009C);
        imp_00607324(cam, d_006120A0);
        sub_0058B970(*(void **)(this + 0x2c8), this + 0x2cc, cam, anim);
        imp_00607330(cam);
        imp_00607330(anim);
    }
    (void)L;
    return 0;
}
