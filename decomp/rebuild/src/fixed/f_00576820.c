/* 0x00576820: reads a packed file into a new buffer (0x005E3B10, size +0x00 plus a terminating 0) and returns it:
 * missing (+0x1C) throws the std::string "Попытка прочитать несуществующий файл" (reading a missing file); the pack is
 * the file's own path (+0x08) when it has a ':', else the game folder (0x006C88B4's +0x04) + "Resource" + the pack
 * number (+0x24, 0x00576720) + ".pak"; an ifstream (binary, shared) seeks to the offset (+0x04, an fpos passed by
 * value) and reads; the path is then set to the folder + "opened_files.log" (unused) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int off, pad0, pos_lo, pos_hi, state, pad1; } Fpos_576820;   /* std::fpos<int> */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void *__cdecl sub_00576720(void *out, int n);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_0061D7FC[], d_0069916C[], d_006C88B4[], d_0060B218[], d_0060B224[], d_0061D7E8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C unsigned int (__thiscall *imp_006072E0)(const void *, char c, unsigned int pos) __asm__("__imp_?find@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIDI@Z");
DECOMP_C const unsigned int *imp_006071C4 __asm__("__imp_?npos@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@2IB");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void (__thiscall *imp_006072DC)(void *, const char *, int, int, int) __asm__("__imp_??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z");
DECOMP_C void *(__thiscall *imp_006072D0)(void *, Fpos_576820) __asm__("__imp_?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@V?$fpos@H@2@@Z");
DECOMP_C void *(__thiscall *imp_006071A0)(void *, char *, int) __asm__("__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");
DECOMP_C void (__thiscall *imp_006071EC)(void *) __asm__("__imp_?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");
DECOMP_C void (__thiscall *imp_006071D4)(void *) __asm__("__imp_??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ");

DECOMP(00576820)
char *__thiscall f_00576820(void *this)
{
    char *s = (char *)this, *buf, *dir = *(char **)d_006C88B4 + 4;
    unsigned int path[7], num[7], a[7], b[7], c[7];
    unsigned int f[0x90 / 4];
    Fpos_576820 pos;
    if (!*(int *)(s + 0x1c)) {
        unsigned int msg[7], thrown[7];         /* two std::string */
        imp_00607324(msg, d_0061D7FC);
        imp_00607334(thrown, msg);
        sub_005E3EC0(thrown, d_0069916C);
    }
    buf = sub_005E3B10(*(unsigned int *)s + 1);
    imp_006071E0(path);
    if (imp_006072E0(s + 8, ':', 0) == *imp_006071C4) {
        void *n = sub_00576720(num, *(int *)(s + 0x24));
        imp_006071DC(c, imp_006071C0(b, imp_006071DC(a, dir, d_0060B218), n), d_0060B224);
        imp_0060731C(path, c);
        imp_00607330(c);
        imp_00607330(b);
        imp_00607330(a);
        imp_00607330(num);
    } else
        imp_0060731C(path, s + 8);
    imp_006072DC(f, imp_0060732C(path), 0x21, 0x40, 1);
    pos.off = *(unsigned int *)(s + 4);
    pos.pos_lo = 0;
    pos.pos_hi = 0;
    pos.state = 0;
    imp_006072D0(f, pos);
    imp_006071A0(f, buf, *(int *)s);
    imp_006071EC(f);
    imp_006071DC(a, dir, d_0061D7E8);
    imp_0060731C(path, a);
    imp_00607330(a);
    buf[*(unsigned int *)s] = 0;
    imp_006071D4(f);
    imp_00607330(path);
    return buf;
}
