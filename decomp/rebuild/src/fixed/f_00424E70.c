/* 0x00424E70: the camera singleton (0x006C8708): created on first use by allocating 0x244 bytes and constructing
 * them (0x00435E70); a construction that yields nothing throws the Singleton.h error (the string at 0x00607BC8,
 * file 0x00607BAC, line 0x10).  Returns the singleton. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00435E70(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void *d_006C8708;
DECOMP_C char d_00607BC8[], d_00607BAC[], d_0069916C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");

DECOMP(00424E70)
void *__cdecl f_00424E70(void)
{
    if (!d_006C8708) {
        void *camera = sub_005E3EAE(0x244);
        d_006C8708 = camera ? sub_00435E70(camera) : 0;
        if (!d_006C8708) {
            unsigned int msg[7], exc[9];
            imp_00607324(msg, d_00607BC8);
            sub_00421220(exc, msg, d_00607BAC, 0x10);
            sub_005E3EC0(exc, d_0069916C);
        }
    }
    return d_006C8708;
}
