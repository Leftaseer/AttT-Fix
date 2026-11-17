/* 0x004C5210: destroys the secondary object at 0x6ca4b4 and releases the two interface singletons. */
#include "auto_pre.h"
typedef void (__stdcall *release_4C5210)(void *self);
DECOMP_C void __thiscall sub_004C4D60(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *memory);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *object, void *throw_info);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_006CA4AC[], d_006CA4B4[], d_006CA4A4[];
DECOMP_C char d_00611400[], d_006113F0[], d_0069916C[];

DECOMP(004C5210)
void __cdecl f_004C5210(void)
{
    void *object;
    if (!*(void **)d_006CA4AC) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_00611400);
        sub_00421220(thrown, msg, d_006113F0, 0x52f);
        sub_005E3EC0(thrown, d_0069916C);
        __builtin_unreachable();
    }
    object = *(void **)d_006CA4B4;
    if (object) {
        sub_004C4D60(object);
        sub_005E3E9C(object);
        *(void **)d_006CA4B4 = 0;
    }
    object = *(void **)d_006CA4AC;
    if (object) {
        ((release_4C5210)(*(void ***)object)[0x8 / 4])(object);
        *(void **)d_006CA4AC = 0;
    }
    object = *(void **)d_006CA4A4;
    if (object) {
        ((release_4C5210)(*(void ***)object)[0x8 / 4])(object);
        *(void **)d_006CA4A4 = 0;
    }
}
