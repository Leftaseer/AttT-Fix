/* 0x004C1EB0: while the singleton at 0x6CA4AC is missing, throws "..." (the string at 0x00611400, the exception
 * object built by 0x00421220 with file 0x006113F0 and line 0x8BB, 0x005E3EC0 with the throw info at 0x0069916C);
 * otherwise the stack argument is returned unchanged (the original simply reloads [esp+4]).  Nothing in the image
 * calls, jumps to or points at this function. */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);       /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_006CA4AC[], d_00611400[], d_006113F0[], d_0069916C[];

DECOMP(004C1EB0)
void *__cdecl f_004C1EB0(void *value)
{
    if (!*(void **)d_006CA4AC) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_00611400);
        sub_00421220(thrown, msg, d_006113F0, 0x8bb);
        sub_005E3EC0(thrown, d_0069916C);
    }
    return value;
}
