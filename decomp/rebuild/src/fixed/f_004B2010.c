/* 0x004B2010: CScene::~CScene: the vtables (CScene, its collector at +4), clears the global collector at +0x54
 * (vf18) and the collector at +4 (0x0043B8D0), destroys +0x54 (0x0044D7D0), releases the dialog at +0x44 (its count
 * at +8, the deleting destructor of its +4), the string at +0x1C and the collector at +4; then the base vtable */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0043B8D0(void *self);
DECOMP_C void __thiscall sub_0044D7D0(void *self);
DECOMP_C char d_0061095C[], d_00610938[], d_0061092C[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *vf18_4B2010)(void *self);
typedef void (__thiscall *dtor_4B2010)(void *self, int flags);

DECOMP(004B2010)
void __thiscall f_004B2010(void *this)
{
    char *s = (char *)this;
    char *d;
    *(void **)s = d_0061095C;
    *(void **)(s + 4) = d_00610938;
    ((vf18_4B2010)(*(void ***)(s + 0x54))[0x18 / 4])(s + 0x54);
    sub_0043B8D0(s + 4);
    sub_0044D7D0(s + 0x54);
    d = *(char **)(s + 0x44);
    if (d && --*(int *)(d + 8) == 0)
        ((dtor_4B2010)(*(void ***)(d + 4))[0])(d + 4, 1);
    imp_00607330(s + 0x1c);
    sub_0044D7D0(s + 4);
    *(void **)s = d_0061092C;
}
