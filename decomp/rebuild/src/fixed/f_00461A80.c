/* 0x00461A80: Glow::Render (cdecl, the drawn object as its only argument): a null object throws "Glow::Render :
 * Argument cannot be NULL" and a null Glow singleton (0x006C8E74) throws "... Class must be initialized before
 * call" (both from .\Glow.cpp lines 0x0A and 0x0B through 0x00421220 and 0x005E3EC0 with info 0x0069916C).  The
 * world-view matrix is the hero's (0x00425F60 +0x168) times the camera's (0x00424E70 +0x88) and the projection is
 * the camera's +0xC8; both are given to the Glow by name (vtable +0x50), then its pass count (vtable +0x18 with a 0)
 * is walked with a pass begin (+0x20), the object's own draw (+0xC8) and a pass end (+0x24) each, and the effect is
 * ended (+0x1C).  The Glow pointer is reloaded for every virtual call. */
/* @conv - 0 */
#include "auto_pre.h"

typedef struct { unsigned int w[7]; } Str_461A80;                  /* std::string */
typedef void (__thiscall *setmat_461A80)(void *self, const char *name, void *matrix);
typedef void (__thiscall *begin_461A80)(void *self, unsigned int *count, int unused);
typedef void (__thiscall *pass_461A80)(void *self, unsigned int index);
typedef void (__thiscall *end_461A80)(void *self);
typedef void (__thiscall *draw_461A80)(void *self);

DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b); /* D3DXMatrixMultiply */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);  /* _CxxThrowException */
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C char d_006C8E74[], d_0060BCD0[], d_0060BCC4[], d_0060BC8C[], d_0060BC80[], d_0060BC74[], d_0069916C[];

DECOMP(00461A80)
void __cdecl f_00461A80(void *arg)
{
    float matrix[16];
    unsigned int count, i;
    char *glow, *hero, *cam, *cam2;

    if (!arg) {
        Str_461A80 msg;
        unsigned int exc[7];
        imp_00607324(&msg, d_0060BCD0);
        sub_00421220(exc, &msg, d_0060BCC4, 0xa);
        sub_005E3EC0(exc, d_0069916C);
    }
    if (!*(void **)d_006C8E74) {
        Str_461A80 msg;
        unsigned int exc[7];
        imp_00607324(&msg, d_0060BC8C);
        sub_00421220(exc, &msg, d_0060BCC4, 0xb);
        sub_005E3EC0(exc, d_0069916C);
    }
    hero = (char *)sub_00425F60();
    cam = (char *)sub_00424E70();
    cam2 = (char *)sub_00424E70();
    sub_005B8020(matrix, hero + 0x168, cam + 0x88);
    glow = *(char **)d_006C8E74;
    (*(setmat_461A80)(*(void ***)glow)[0x50 / 4])(glow, d_0060BC80, matrix);
    glow = *(char **)d_006C8E74;
    (*(setmat_461A80)(*(void ***)glow)[0x50 / 4])(glow, d_0060BC74, cam2 + 0xc8);
    glow = *(char **)d_006C8E74;
    (*(begin_461A80)(*(void ***)glow)[0x18 / 4])(glow, &count, 0);
    for (i = 0; i < count; i++) {
        glow = *(char **)d_006C8E74;
        (*(pass_461A80)(*(void ***)glow)[0x20 / 4])(glow, i);
        (*(draw_461A80)(*(void ***)arg)[0xc8 / 4])(arg);
        glow = *(char **)d_006C8E74;
        (*(end_461A80)(*(void ***)glow)[0x24 / 4])(glow);
    }
    glow = *(char **)d_006C8E74;
    (*(end_461A80)(*(void ***)glow)[0x1c / 4])(glow);
}
