/* 0x004C3080: opens a wave file through the MMIO "MMIO" IO procedure (.\Sound.cpp): a null name throws
 * "strFileName" (0x004C1D00 with E_INVALIDARG, line 0x31), the buffer at +0 is deleted and cleared, the
 * zeroed MMIOINFO gets fccIOProc "MMIO", the mmioOpenA handle goes to +4 (a zero handle throws
 * "Error opening wave file '<name>'" from line 0x3E) and the wave header is read (0x004C1FB0 descends into
 * the chunks, 0x004C2410 fills the format) before +0x30 is set from +0xC.  Both exceptions carry the throw
 * info 0x0069916C and are created by 0x004C1D00 / 0x00421220. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4C3080;                  /* std::string */
typedef struct { unsigned int w[0x48 / 4]; } Info_4C3080;          /* MMIOINFO */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                        /* operator delete[] */
DECOMP_C void *__cdecl sub_005E40BE(void *p, int c, unsigned int n);/* memset */
DECOMP_C void __thiscall sub_004C1D00(void *exc, unsigned int hr, void *msg, const char *file, int line);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);  /* _CxxThrowException */
DECOMP_C void __thiscall sub_004C1FB0(void *self);                  /* descends into the wave chunks */
DECOMP_C void __thiscall sub_004C2410(void *self);                  /* reads the wave format */
DECOMP_C void *(__stdcall *imp_0060770C)(const char *, void *, unsigned int) __asm__("__imp__mmioOpenA");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C char d_006115AC[], d_00611590[], d_0060B008[], d_006113F0[], d_0069916C[];

DECOMP(004C3080)
void __thiscall f_004C3080(char *this, const char *name)
{
    Info_4C3080 info;
    Str_4C3080 msg, part, text;
    unsigned int exc[8];

    if (!name) {
        imp_00607324(&msg, d_006115AC);                            /* "strFileName" */
        sub_004C1D00(exc, 0x80070057, &msg, d_006113F0, 0x31);
        sub_005E3EC0(exc, d_0069916C);
    }
    if (*(void **)this) {
        sub_005E3EBA(*(void **)this);
        *(void **)this = 0;
    }
    info.w[0] = 0;                                                 /* dwFlags */
    sub_005E40BE((char *)&info + 4, 0, 0x44);
    *(unsigned int *)((char *)&info + 4) = 0x4F494D4D;             /* fccIOProc "MMIO" */
    *(void **)(this + 4) = imp_0060770C(name, &info, 0x10000);
    if (!*(void **)(this + 4)) {
        imp_00607324(&part, d_00611590);                           /* "Error opening wave file '" */
        imp_006071DC(&text, &part, name);
        imp_006071DC(&msg, &text, d_0060B008);                     /* "'" */
        sub_00421220(exc, &msg, d_006113F0, 0x3e);                 /* .\Sound.cpp:62 */
        sub_005E3EC0(exc, d_0069916C);
    }
    sub_004C1FB0(this);
    sub_004C2410(this);
    *(unsigned int *)(this + 0x30) = *(unsigned int *)(this + 0xc);
}
