/* 0x00426DF0: the alpha control manager's constructor: the control base is built with the name at 0x0060FA8B, the
 * 0x0060819C vtable follows, the +0x58 part and its list created, the pick position and table from the two
 * singletons, and the +0x49 flag set. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int *__thiscall sub_004AB9C0(void *self, void *name, unsigned int z);
DECOMP_C unsigned int __stdcall sub_004C2F40(void);
DECOMP_C unsigned int __stdcall sub_004215D0(void);
DECOMP_C unsigned int __stdcall sub_00421680(void);
DECOMP_C char d_0060819C[], d_0060FA8B[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00426DF0)
void *__thiscall f_00426DF0(void *this)
{
    char *s = (char *)this;
    unsigned int name[7];

    imp_00607324(name, d_0060FA8B);
    sub_004AB9C0(s, name, 0);
    imp_00607330(name);
    *(const void **)s = d_0060819C;
    *(unsigned int *)(s + 0x5c) = sub_004C2F40();
    *(unsigned int *)(s + 0x60) = 0;
    *(unsigned int *)(s + 0x68) = sub_004215D0();
    *(unsigned int *)(s + 0x64) = sub_00421680();
    *(float *)(s + 0x70) = 0.0f;
    s[0x49] = 1;
    *(unsigned int *)(s + 0x6c) = 0;
    return s;
}
