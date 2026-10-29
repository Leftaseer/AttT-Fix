/* 0x005302E0: loads the grass map (+0x0C, 0x00431730 by file name) or, when it is missing, builds it with progress on a
 * console (AllocConsole, 0x00485690 placing it): the mask index map (0x0052D140 from the level name: a w x h grid of
 * 16-bit indices) and the detailed masks (0x005B7C30: index 0 = no grass, 1 = grass, n = mask n - 2 of 20 x 20 cells,
 * bit rows of 12-byte entries, width +4 / height +8) fill a 20w x 20h bit map (0x00431960; rows of 12-byte entries);
 * the index map is freed and the result saved to Resource/Grass/ plus the file name under the data root
 * (0x00427990 + 0x20, 0x00431440) */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5302E0;                 /* std::string */
DECOMP_C unsigned char __thiscall sub_00431730(void *self, void *name);
DECOMP_C void __cdecl sub_00485690(int a, int b, int c, int d);
DECOMP_C unsigned short **__thiscall sub_0052D140(void *self, Str_5302E0 name, unsigned short *w, unsigned short *h);
DECOMP_C char *__thiscall sub_005B7C30(void *self);
DECOMP_C void __thiscall sub_00431960(void *self, unsigned int w, unsigned int h);
DECOMP_C void __thiscall sub_00431440(void *self, void *name);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __cdecl sub_005E3EBA(void *p);                /* operator delete[] */
DECOMP_C char d_00615588[], d_0061556C[], d_00615544[], d_00615528[], d_00615518[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C int (__stdcall *imp_006070AC)(void) __asm__("__imp__AllocConsole@0");
DECOMP_C int (__stdcall *imp_00607104)(void) __asm__("__imp__FreeConsole@0");
DECOMP_C void *(__stdcall *imp_00607118)(unsigned int) __asm__("__imp__GetStdHandle@4");
DECOMP_C int (__stdcall *imp_0060710C)(void *, const void *, unsigned int, unsigned int *, void *) __asm__("__imp__WriteFile@20");
DECOMP_C int (__stdcall *imp_0060711C)(void *, unsigned int) __asm__("__imp__SetConsoleCursorPosition@8");
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");

static void say_5302E0(const char *text, unsigned int n, unsigned int *done)
{
    imp_0060710C(imp_00607118(0xfffffff5), text, n, done, 0);   /* STD_OUTPUT_HANDLE */
}

DECOMP(005302E0)
void __thiscall f_005302E0(void *this, void *file, void *level)
{
    char *s = (char *)this, *g = s + 0xc, *masks;
    unsigned short w, h, **idx;
    unsigned int done, r, c, off, rows, hh;
    if (sub_00431730(g, file))
        return;
    imp_006070AC();
    sub_00485690(0, 0, 600, 300);
    sub_00485690(0, 600, 400, 700);
    say_5302E0(d_00615588, 0x1a, &done);
    {
        Str_5302E0 n;
        imp_00607334(&n, level);
        idx = sub_0052D140(this, n, &w, &h);
    }
    imp_0060711C(imp_00607118(0xfffffff5), 0);
    say_5302E0(d_0061556C, 0x1a, &done);
    masks = sub_005B7C30(this);
    hh = h;
    sub_00431960(g, w * 20, hh * 20);
    imp_0060711C(imp_00607118(0xfffffff5), 0);
    say_5302E0(d_00615544, 0x24, &done);
    rows = *(unsigned int *)(s + 0x14);
    for (r = 0, off = 0; r < rows; r++, off += 0xc) {
        char buf[0x100];
        unsigned int len, my = r / 20;
        imp_006073D0(buf, d_00615528, r, rows);
        imp_0060711C(imp_00607118(0xfffffff5), 0x10000);       /* COORD {0, 1} */
        for (len = 0; buf[len]; len++)
            ;
        say_5302E0(buf, len, &done);
        for (c = 0; c < *(unsigned int *)(s + 0x10); c++) {
            unsigned int mx = c / 20, v = idx[my][mx];
            unsigned char bit, m, *p;
            if (v == 0)
                bit = 0;
            else if (v == 1)
                bit = 1;
            else {
                unsigned int *mk = (*(unsigned int ***)(masks + 4))[v - 2];
                unsigned int lx = c - mx * 20, ly = r - my * 20;
                if (lx <= mk[1] && ly <= mk[2])
                    bit = (((unsigned char *)((unsigned int *)mk[0])[ly * 3])[lx >> 3] & (1 << (lx & 7))) != 0;
                else
                    bit = 0;
            }
            m = (unsigned char)(1 << ((unsigned char)c & 7));
            p = (unsigned char *)(*(unsigned int *)(*(char **)g + off) + (c >> 3));
            if (bit)
                *p |= m;
            else
                *p &= ~m;
        }
        rows = *(unsigned int *)(s + 0x14);
    }
    imp_00607104();
    if (h) {
        unsigned short **p = idx;
        for (; hh; hh--, p++)
            if (*p) {
                sub_005E3EBA(*p);
                *p = 0;
            }
    }
    if (idx)
        sub_005E3EBA(idx);
    {
        unsigned int a[7], b[7];
        imp_006071DC(a, sub_00427990() + 0x20, d_00615518);
        sub_00431440(g, imp_006071C0(b, a, file));
        imp_00607330(b);
        imp_00607330(a);
    }
}
