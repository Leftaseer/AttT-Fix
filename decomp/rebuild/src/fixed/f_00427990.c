/* 0x00427990: CSingleton<CConfig>::instance: the config object at 0x006C884C is built on first use (operator new
 * 0x005E3EAE of 0x98 bytes, constructor 0x00441D10); a failed allocation or construction throws the
 * CSingleton.h line 16 exception of 0x00421220. Returns the instance. */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00441D10(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);       /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_00607BC8[], d_00607E98[], d_0069916C[];
DECOMP_C void *d_006C884C;

DECOMP(00427990)
void *__cdecl f_00427990(void)
{
    if (!d_006C884C) {
        void *config = sub_005E3EAE(0x98);
        d_006C884C = config ? sub_00441D10(config) : 0;
        if (!d_006C884C) {
            unsigned int msg[7], thrown[7];
            imp_00607324(msg, d_00607BC8);
            sub_00421220(thrown, msg, d_00607E98, 0x10);
            sub_005E3EC0(thrown, d_0069916C);
            __builtin_unreachable();
        }
    }
    return d_006C884C;
}
