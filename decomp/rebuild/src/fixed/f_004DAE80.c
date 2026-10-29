/* 0x004DAE80: builds the map of triangle tessellation levels (into vector-of-vectors arg 1, from the distance list
 * arg 2) with progress on a console (AllocConsole, its window placed 600 x 300): the squared distances (0x004D6110),
 * one list per triangle (+0x38: 6-byte index triples; 0x00481FD0); for each triangle a strstream line "Processing
 * triangle number i from n" goes to the console (row 2), its geometry (0x004D4370) is compared against every
 * triangle (0x004D4400 with the squared distances) and the level byte with the 14-bit index appended (push_back
 * inline: 0x00442FC0 / 0x00553970); at the end "Build complete!", the console cleared and the map saved (0x004D5010) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004D6110(void *self, unsigned int n, const float *val);
DECOMP_C void __thiscall sub_00481FD0(void *self, unsigned int n, unsigned int v0, unsigned int v1, unsigned int v2,
                                      unsigned int v3);
DECOMP_C void *__cdecl sub_00447860(void *os, const char *s);
DECOMP_C void __cdecl sub_004D48D0(void *os, int a);
DECOMP_C void __thiscall sub_004D4370(void *self, void *out, void *tri);
DECOMP_C void __thiscall sub_004D6040(void *self, unsigned int n);
DECOMP_C unsigned char __thiscall sub_004D4400(void *self, void *geo, unsigned int k, void *sq, int a);
DECOMP_C void __cdecl sub_00442FC0(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);
DECOMP_C void __thiscall sub_00553970(void *self, void *where, unsigned int n, void *val);
DECOMP_C void __thiscall sub_004D5010(void *self, void *map);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_00612380[], d_0060A240[], d_0060A238[], d_0060A234[], d_0061227C[], d_00612260[], d_00612348[];
DECOMP_C void (__thiscall *imp_0060717C)(void *) __asm__("__imp_??0?$basic_ios@DU?$char_traits@D@std@@@std@@IAE@XZ");
DECOMP_C void (__thiscall *imp_00607180)(void *, void *, int) __asm__("__imp_??0?$basic_iostream@DU?$char_traits@D@std@@@std@@QAE@PAV?$basic_streambuf@DU?$char_traits@D@std@@@1@@Z");
DECOMP_C void (__thiscall *imp_00607184)(void *, int) __asm__("__imp_??0strstreambuf@std@@QAE@H@Z");
DECOMP_C void (__thiscall *imp_006071AC)(void *) __asm__("__imp_??1strstreambuf@std@@UAE@XZ");
DECOMP_C void (__thiscall *imp_0060718C)(void *) __asm__("__imp_??1?$basic_iostream@DU?$char_traits@D@std@@@std@@UAE@XZ");
DECOMP_C void (__thiscall *imp_00607188)(void *) __asm__("__imp_??1?$basic_ios@DU?$char_traits@D@std@@@std@@UAE@XZ");
DECOMP_C char *(__thiscall *imp_006071D0)(void *) __asm__("__imp_?str@strstreambuf@std@@QAEPADXZ");
DECOMP_C void *(__thiscall *imp_00607370)(void *, unsigned long) __asm__("__imp_??6?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV01@K@Z");
DECOMP_C void *(__thiscall *imp_0060736C)(void *, unsigned int) __asm__("__imp_??6?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV01@I@Z");
DECOMP_C void *(__thiscall *imp_006072B8)(void *, void *) __asm__("__imp_??6?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV01@P6AAAV01@AAV01@@Z@Z");
DECOMP_C void *imp_006072C0 __asm__("__imp_?endl@std@@YAAAV?$basic_ostream@DU?$char_traits@D@std@@@1@AAV21@@Z");
DECOMP_C int (__stdcall *imp_006070AC)(void) __asm__("__imp__AllocConsole@0");
DECOMP_C unsigned int (__stdcall *imp_006070B0)(char *, unsigned int) __asm__("__imp__GetConsoleTitleA@8");
DECOMP_C void *(__stdcall *imp_0060765C)(const char *, const char *) __asm__("__imp__FindWindowA@8");
DECOMP_C int (__stdcall *imp_00607660)(void *, void *, int, int, int, int, unsigned int) __asm__("__imp__SetWindowPos@28");
DECOMP_C void *(__stdcall *imp_00607118)(unsigned int) __asm__("__imp__GetStdHandle@4");
DECOMP_C int (__stdcall *imp_0060710C)(void *, const void *, unsigned int, unsigned int *, void *) __asm__("__imp__WriteFile@20");
DECOMP_C int (__stdcall *imp_0060711C)(void *, unsigned int) __asm__("__imp__SetConsoleCursorPosition@8");
DECOMP_C void (__stdcall *imp_006070FC)(unsigned int) __asm__("__imp__Sleep@4");
DECOMP_C int (__stdcall *imp_00607110)(void *, void *) __asm__("__imp__GetConsoleScreenBufferInfo@8");
DECOMP_C int (__stdcall *imp_00607114)(void *, char, unsigned int, unsigned int, unsigned int *) __asm__("__imp__FillConsoleOutputCharacterA@20");

#define OUT imp_00607118(0xfffffff5)                /* STD_OUTPUT_HANDLE */
#define TRIS (*(char **)(s + 0x38))
#define NTRI (*(char **)(TRIS + 4) ? (unsigned int)((*(char **)(TRIS + 8) - *(char **)(TRIS + 4)) / 6) : 0)

DECOMP(004DAE80)
void __thiscall f_004DAE80(void *this, char *map, char *dist)
{
    char *s = (char *)this;
    struct { unsigned int alloc; float *begin, *end, *cap; } sq;
    unsigned char area[0x100], geo[0x18];
    unsigned int done, written, t, off6 = 0, off16 = 0, n;
    unsigned short i;
    float zero = 0.0f;
    char *str;
    n = *(char **)(dist + 4) ? (unsigned int)((*(char **)(dist + 8) - *(char **)(dist + 4)) >> 2) : 0;
    sub_004D6110(&sq, n, &zero);
    for (i = 0; i < (unsigned int)(sq.begin ? sq.end - sq.begin : 0); i++) {
        float d = (*(float **)(dist + 4))[i];
        sq.begin[i] = d * d;
    }
    sub_00481FD0(map, NTRI, 0, 0, 0, 0);
    imp_006070AC();
    imp_006070B0((char *)area, 0xff);
    imp_0060765C(0, (char *)area);
    imp_00607660(imp_0060765C(0, (char *)area), 0, 0, 0, 600, 300, 0);
    imp_0060710C(OUT, d_00612380, 0x34, &written, 0);
    for (t = 0; t < NTRI; t++, off6 += 6, off16 += 0x10) {
        char *ss = (char *)area, *sb = ss + 0xc, *el;
        void *os;
        unsigned short k;
        *(void **)ss = d_0060A240;
        *(void **)(ss + 8) = d_0060A238;
        imp_0060717C(ss + 0x60);
        imp_00607180(ss, sb, 0);
        *(void **)(ss + (*(int **)ss)[1]) = d_0060A234;
        imp_00607184(sb, 0);
        os = sub_00447860(ss + 8, d_00612260);
        os = imp_00607370(os, t + 1);
        os = sub_00447860(os, d_0061227C);
        os = imp_0060736C(os, NTRI);
        os = imp_006072B8(os, imp_006072C0);
        sub_004D48D0(os, 0);
        imp_0060711C(OUT, 0x20000);                 /* COORD {0, 2} */
        str = imp_006071D0(sb);
        {
            unsigned int len = 0;
            while (str[len])
                len++;
            imp_0060710C(OUT, str, len, &done, 0);
        }
        sub_004D4370(this, geo, *(char **)(TRIS + 4) + off6);
        sub_004D6040(*(char **)(map + 4) + off16, NTRI);
        for (k = 0; k < NTRI; k++) {
            unsigned char val[4];
            char *v;
            *(unsigned short *)val = k & 0x3fff;
            val[2] = sub_004D4400(this, geo, k, &sq, 1);
            v = *(char **)(map + 4) + off16;
            el = *(char **)(v + 4);
            if (el && (unsigned int)((*(char **)(v + 8) - el) >> 2) < (unsigned int)((*(char **)(v + 0xc) - el) >> 2)) {
                unsigned int x = written & 0xffffff00;
                sub_00442FC0((void *)(size_t)x, *(char **)(v + 8), 1, val, (unsigned int)(size_t)v,
                             (void *)(size_t)done, x);
                *(char **)(v + 8) += 4;
            } else
                sub_00553970(v, *(void **)(v + 8), 1, val);
        }
        *(void **)(ss + (*(int **)ss)[1]) = d_0060A234;
        imp_006071AC(sb);
        imp_0060718C(sb);
        imp_00607188(ss + 0x60);
    }
    imp_0060710C(OUT, d_00612348, 0x35, &written, 0);
    imp_006070FC(1000);
    imp_00607110(OUT, geo);
    imp_00607114(OUT, ' ', (unsigned int)((short *)geo)[1] * (unsigned int)((short *)geo)[0], 0, &written);
    imp_0060711C(OUT, 0);
    sub_004D5010(this, map);
    imp_006070FC(1000);
    if (sq.begin)
        sub_005E3E9C(sq.begin);
}
