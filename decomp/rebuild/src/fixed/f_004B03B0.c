/* 0x004B03B0: constructs a UI resource with a 100-entry record array and an empty string, then loads the supplied element. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004ABA60(void *self, void *name, int shared);
DECOMP_C void __thiscall sub_004AFBF0(void *self, void *element);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char d_0060FA8B[], d_006104AC[], d_006104A4[];

DECOMP(004B03B0)
void *__thiscall f_004B03B0(void *self, void *element)
{
    char *this = self;
    unsigned int name[7];
    imp_00607324(name, d_0060FA8B);
    sub_004ABA60(this, name, 0);
    imp_00607330(name);
    *(char **)this = d_006104AC;
    *(char **)(this + 0x204) = d_006104A4;
    *(void **)(this + 0x208) = sub_005E3B10(100 * 12);
    *(unsigned int *)(this + 0x20c) = 0;
    imp_006071E0(this + 0x210);
    *(unsigned int *)(this + 0x24c) = 0;
    sub_004AFBF0(this, element);
    return this;
}
