/* 0x00445630: DatFile's reader (returns a string; file name): opens the file into its stream (+8, throws "<name> don't
 * be open", DatFile.cpp:28) and reads it a character at a time (+4, 0 at the end) into its text (+0x94): ',', ';' and
 * tabs become one space (a pending space 0x006C8974, none after a line break 0x006C0036), other characters go through
 * 0x00444BD0 in lower case, line comments (two slashes) are skipped to the line end and block comments (slash-star to
 * star-slash) whole, an unfinished one throwing "Comment(...) is not ended"; a lone '/' is kept; the text ends with a
 * line break (replacing a pending space) and a NUL. Returns a copy of the text */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00444BA0(void *self);
DECOMP_C void __thiscall sub_00444BD0(void *self, int c);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C char d_0060A5B8[], d_0060A5A8[], d_0069916C[], d_006C8974[], d_006C0036[], d_0060A58C[], d_0060A570[];
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void (__thiscall *imp_006071F4)(void *, const char *, int, int) __asm__("__imp_?open@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXPBDHH@Z");
DECOMP_C unsigned char (__thiscall *imp_006071F0)(const void *) __asm__("__imp_??7ios_base@std@@QBE_NXZ");
DECOMP_C void *(__thiscall *imp_006071A0)(void *, char *, int) __asm__("__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");
DECOMP_C void (__thiscall *imp_006071EC)(void *) __asm__("__imp_?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void *(__thiscall *imp_00607200)(void *, unsigned int, unsigned int) __asm__("__imp_?erase@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV12@II@Z");
DECOMP_C void *(__thiscall *imp_00607204)(void *, char) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@D@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C int (__cdecl *imp_0060741C)(int) __asm__("__imp__tolower");

#define SPACE (*(unsigned char *)d_006C8974)
#define NEWLINE (*(unsigned char *)d_006C0036)

static int bad_445630(void *is)
{
    char *p = (char *)is;
    return imp_006071F0(p + (*(int **)p)[1]);
}

static void get_445630(char *s)
{
    if (bad_445630(imp_006071A0(s + 8, s + 4, 1)))
        s[4] = 0;
}

static void space_445630(char *s)
{
    if (!SPACE && !NEWLINE) {
        SPACE = 1;
        NEWLINE = 0;
        imp_00607204(s + 0x94, ' ');
    }
}

static void fail_445630(void *msg, int line)
{
    unsigned int thrown[7];
    sub_00421220(thrown, msg, d_0060A5A8, line);
    sub_005E3EC0(thrown, d_0069916C);
}

static void failc_445630(const char *text, int line)
{
    unsigned int msg[7];
    imp_00607324(msg, text);
    fail_445630(msg, line);
}

DECOMP(00445630)
void *__thiscall f_00445630(void *this, void *ret, const void *name)
{
    char *s = (char *)this, c;
    int st = 0;
    imp_006071F4(s + 8, imp_0060732C(name), 1, 0x40);
    if (bad_445630(s + 8)) {
        unsigned int msg[7];
        fail_445630(imp_006071DC(msg, name, d_0060A5B8), 0x1c);
    }
    get_445630(s);
    for (;;) {
        c = s[4];
        if (st == 0) {
            if (!c)
                break;
            if (c == ',' || c == ';' || c == '\t') {
                space_445630(s);
                get_445630(s);
            } else if (c == '/') {
                sub_00444BA0(this);
                st = 1;
            } else {
                sub_00444BD0(this, imp_0060741C(c));
                sub_00444BA0(this);
            }
        } else if (st == 1) {
            if (c == '/') {
                space_445630(s);
                get_445630(s);
                st = 2;
            } else if (c == '*') {
                space_445630(s);
                sub_00444BA0(this);
                st = 3;
            } else {
                if (!c)
                    failc_445630(d_0060A58C, 0x51);
                NEWLINE = 0;
                SPACE = 0;
                imp_00607204(s + 0x94, '/');
                st = 0;
            }
        } else if (st == 2) {
            if (!c || c == '\n')
                st = 0;
            else
                sub_00444BA0(this);
        } else if (st == 3) {
            if (!c)
                failc_445630(d_0060A570, 0x68);
            get_445630(s);
            if (c == '*')
                st = 4;
        } else if (st == 4) {
            if (!c)
                failc_445630(d_0060A570, 0x79);
            get_445630(s);
            st = c == '/' ? 0 : 3;
        }
    }
    if (SPACE == 1) {
        SPACE = 0;
        NEWLINE = 1;
        imp_00607200(s + 0x94, *(unsigned int *)(s + 0xa8) - 1, 1);
        imp_00607204(s + 0x94, '\n');
    } else if (!NEWLINE) {
        NEWLINE = 1;
        imp_00607204(s + 0x94, '\n');
    }
    NEWLINE = 0;
    SPACE = 0;
    imp_00607204(s + 0x94, 0);
    imp_006071EC(s + 8);
    imp_00607334(ret, s + 0x94);
    return ret;
}
