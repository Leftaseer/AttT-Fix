/* 0x00479B30: constructs the 2D resource with an empty name, installs the vtable, finishes common initialization and loads the supplied element. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004ABA60(void *self, void *name, int shared);
DECOMP_C void __thiscall sub_00479930(void *self);
DECOMP_C void __thiscall sub_004AB810(void *self, void *element, int shared);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_0060FA8B[], d_0060EB6C[];

DECOMP(00479B30)
void *__thiscall f_00479B30(void *this, void *element)
{
    unsigned int name[7];
    imp_00607324(name, d_0060FA8B);
    sub_004ABA60(this, name, 0);
    imp_00607330(name);
    *(char **)this = d_0060EB6C;
    sub_00479930(this);
    sub_004AB810(this, element, 0);
    return this;
}
