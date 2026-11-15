/* 0x00421730: the back buffer texture singleton (0x006C868C): created on first use by allocating 0x14 bytes and
 * constructing them (0x00430130); a construction that yields nothing throws the Singleton.h error (the string at
 * 0x00607BC8, file 0x00607BAC, line 0x10).  Returns the singleton. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00430130(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void *d_006C868C;
DECOMP_C char d_00607BC8[], d_00607BAC[], d_0069916C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");

DECOMP(00421730)
void *__cdecl f_00421730(void)
{
    if (!d_006C868C) {
        void *texture = sub_005E3EAE(0x14);
        d_006C868C = texture ? sub_00430130(texture) : 0;
        if (!d_006C868C) {
            unsigned int msg[7], exc[9];
            imp_00607324(msg, d_00607BC8);
            sub_00421220(exc, msg, d_00607BAC, 0x10);
            sub_005E3EC0(exc, d_0069916C);
        }
    }
    return d_006C868C;
}
