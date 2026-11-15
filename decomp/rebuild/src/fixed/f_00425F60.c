/* 0x00425F60: the ActionScript singleton at 0x006C8EF8.  A missing one raises the Singleton.h error: the message
 * string 0x00607EE8, the exception object (0x00421220 with file 0x00607ED4 and line 0x3D) and 0x005E3EC0 with the
 * throw info at 0x0069916C.  Returns the singleton. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void *d_006C8EF8;
DECOMP_C char d_00607EE8[], d_00607ED4[], d_0069916C[];

DECOMP(00425F60)
void *__cdecl f_00425F60(void)
{
    if (!d_006C8EF8) {
        unsigned int msg[7], exc[9];
        imp_00607324(msg, d_00607EE8);
        sub_00421220(exc, msg, d_00607ED4, 0x3d);
        sub_005E3EC0(exc, d_0069916C);
    }
    return d_006C8EF8;
}
