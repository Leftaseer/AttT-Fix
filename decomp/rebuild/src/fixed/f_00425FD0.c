/* 0x00425FD0: the ActionScript object's constructor: the CRenderObject base with an empty name and no parent
 * (0x004AB9C0), then the vtables 0x00607ED0 / 0x00607F0C / 0x00607F00 and the manager/action at +0x60/+0x6C
 * cleared; the byte at +0x70 clears.  Returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607F0C[], d_00607F00[], d_00607ED0[], d_0060FA8B[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __thiscall sub_004AB9C0(void *self, void *name, int a);

DECOMP(00425FD0)
void *__thiscall f_00425FD0(void *this)
{
    char *s = (char *)this;
    unsigned int name[7];
    imp_00607324(name, d_0060FA8B);
    sub_004AB9C0(s, name, 0);
    imp_00607330(name);
    *(const void **)(s + 0x58) = d_00607ED0;
    *(const void **)s = d_00607F0C;
    *(const void **)(s + 0x58) = d_00607F00;
    *(void **)(s + 0x60) = 0;
    *(void **)(s + 0x6c) = 0;
    s[0x70] = 0;
    return s;
}
