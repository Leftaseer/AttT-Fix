/* 0x00445DB0: CDatFile keyword reader (file, keyword by value, out table, out count, format set): the previous
 * records (+0x298: per record a string array and a float array, +0xBF8 records) are freed; the file is loaded
 * (0x00445AB0) and the keyword (lower-cased) found (0x00445CD0; missing throws for format sets 0 and 1); the
 * format (+0x288[set] entry +0x290: 'w' a word, 'n' a number) is then read either as "{ record record ... }" or as
 * records up to the end of the line (tokens by 0x00445C60 into +8, numbers by 0x004452A0); bad input throws from
 * DatFile.cpp. Returns 1 with the records and their count */
/* @conv ECX 44 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_445DB0;                 /* std::string */
DECOMP_C unsigned char __thiscall sub_00445AB0(void *self, const void *file);
DECOMP_C unsigned char __thiscall sub_00445CD0(void *self, void *kw);
DECOMP_C void __thiscall sub_00445C60(void *self);
DECOMP_C unsigned char __stdcall sub_004452A0(Str_445DB0 tok, float *out);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);             /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                        /* operator delete[] */
DECOMP_C void __stdcall sub_005E4197(void *p, unsigned int size, int n, void *ctor, void *dtor);
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C char d_0060A684[], d_0060A5A8[], d_0069916C[], d_0060A66C[], d_0060A660[], d_0060A65C[], d_0060A658[],
    d_0060FA8B[], d_0060A634[], d_0060A610[], d_0060A600[], d_0060A5EC[], d_0060A5E4[], d_0060A5D4[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
DECOMP_C void *(__cdecl *imp_006071D8)(void *, const char *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBDABV10@@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_0060720C)(void *, const void *, char) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@D@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C int (__cdecl *imp_tolower)(int) __asm__("__imp__tolower");

#define COUNT (*(unsigned int *)(this + 0xbf8))
#define WORDS(i) (*(Str_445DB0 **)(this + 0x298 + (i) * 8))
#define NUMS(i) (*(float **)(this + 0x29c + (i) * 8))
#define TOK (this + 8)

/* the current format entry and its format string */
static char *fmt_445DB0(char *this)
{
    return *(char **)(this + 0x288 + *(int *)(this + 0x284) * 4) + *(int *)(this + 0x290) * 0x38;
}

#define FMTLEN (*(unsigned int *)(fmt_445DB0(this) + 0x30))
#define FMTCHR(i) (*imp_00607208(fmt_445DB0(this) + 0x1c, (i)))

static void throw_445DB0(void *msg, int line)
{
    unsigned int exc[7];
    sub_00421220(exc, msg, d_0060A5A8, line);
    sub_005E3EC0(exc, d_0069916C);
}

/* "<what><keyword>' in file '<file>'" */
static void keyword_445DB0(const char *what, void *kw, const void *file, int line)
{
    Str_445DB0 a, b, c, d;
    imp_006071D8(&a, what, kw);
    imp_006071DC(&b, &a, d_0060A660);
    imp_006071C0(&c, &b, file);
    imp_0060720C(&d, &c, '\'');
    throw_445DB0(&d, line);
}

/* "Error in file '<file>' after keyword '<keyword>' - '<token>' is not number" */
static void number_445DB0(const void *file, void *kw, void *tok, int line)
{
    Str_445DB0 a, b, c, d, e, f;
    imp_006071D8(&a, d_0060A600, file);
    imp_006071DC(&b, &a, d_0060A5EC);
    imp_006071C0(&c, &b, kw);
    imp_006071DC(&d, &c, d_0060A5E4);
    imp_006071C0(&e, &d, tok);
    imp_006071DC(&f, &e, d_0060A5D4);
    throw_445DB0(&f, line);
}

/* new[] of n elements of size, saturating like the original */
static unsigned int size_445DB0(unsigned int n, unsigned int size, unsigned int extra)
{
    unsigned long long s = (unsigned long long)n * size;
    unsigned int r = s > 0xffffffffu ? 0xffffffffu : (unsigned int)s;
    if (extra)
        r = r + extra < r ? 0xffffffffu : r + extra;
    return r;
}

/* the arrays of the record COUNT: w words, n numbers */
static void alloc_445DB0(char *this, unsigned int w, unsigned int n)
{
    if (w) {
        unsigned int *p = (unsigned int *)sub_005E3B10(size_445DB0(w, 0x1c, 4));
        Str_445DB0 *a = 0;
        if (p) {
            p[0] = w;
            a = (Str_445DB0 *)(p + 1);
            sub_005E4197(a, 0x1c, (int)w, (void *)imp_006071E0, (void *)imp_00607330);
        }
        WORDS(COUNT) = a;
    }
    if (n)
        NUMS(COUNT) = (float *)sub_005E3B10(size_445DB0(n, 4, 0));
}

/* the current token as format character c of the record: returns 0 for a number that is not one */
static int field_445DB0(char *this, char c, int *wi, int *ni)
{
    if (c == 'w') {
        imp_0060731C(&WORDS(COUNT)[*wi], TOK);
        (*wi)++;
    } else if (c == 'n') {
        Str_445DB0 t;
        float f;
        imp_00607334(&t, TOK);
        if (!sub_004452A0(t, &f))
            return 0;
        NUMS(COUNT)[*ni] = f;
        (*ni)++;
    }
    return 1;
}

DECOMP(00445DB0)
unsigned char __thiscall f_00445DB0(void *self, const void *file, unsigned int k0, unsigned int k1, unsigned int k2,
                                    unsigned int k3, unsigned int k4, unsigned int k5, unsigned int k6,
                                    void **out_tbl, unsigned int *out_n, int set)
{
    char *this = (char *)self;
    Str_445DB0 *kw = (Str_445DB0 *)((char *)__builtin_frame_address(0) + 8 + 4 * 1);
    unsigned int i, w = 0, n = 0;
    unsigned char nl;

    *(int *)(this + 0x284) = set;
    for (i = 0; i < COUNT; i++) {
        Str_445DB0 *s = WORDS(i);
        if (s) {
            sub_005E4134(s, 0x1c, ((int *)s)[-1], (void *)imp_00607330);
            sub_005E3EBA((int *)s - 1);
            WORDS(i) = 0;
        }
        if (NUMS(i)) {
            sub_005E3EBA(NUMS(i));
            NUMS(i) = 0;
        }
    }
    COUNT = 0;
    if (!sub_00445AB0(this, file)) {
        Str_445DB0 a, b;
        imp_006071D8(&a, d_0060A684, file);
        imp_0060720C(&b, &a, '\'');
        throw_445DB0(&b, 0x124);
    }
    for (i = 0; i < kw->w[5]; i++) {
        char *p = imp_00607208(kw, i), *q = imp_00607208(kw, i);
        *q = (char)imp_tolower(*p);
    }
    if (!sub_00445CD0(this, kw) && (set == 0 || set == 1))
        keyword_445DB0(d_0060A66C, kw, file, 0x12e);
    nl = 0;
    sub_00445C60(this);
    if (this[4] == '\n')
        nl = 1;
    if (imp_006071E4(TOK, d_0060A65C)) {
        for (i = 0; i < FMTLEN; i++) {
            if (FMTCHR(i) == 'w')
                w++;
            else if (FMTCHR(i) == 'n')
                n++;
        }
        sub_00445C60(this);
        while (imp_00607214(TOK, d_0060A658)) {
            int wi = 0, ni = 0;
            if (imp_006071E4(TOK, d_0060FA8B))
                keyword_445DB0(d_0060A634, kw, file, 0x147);
            alloc_445DB0(this, w, n);
            for (i = 0; i < FMTLEN; i++) {
                if (imp_006071E4(TOK, d_0060FA8B))
                    keyword_445DB0(d_0060A610, kw, file, 0x154);
                if (!field_445DB0(this, FMTCHR(i), &wi, &ni))
                    number_445DB0(file, kw, TOK, 0x15e);
                sub_00445C60(this);
            }
            COUNT++;
        }
    } else {
        unsigned char done = 0;
        for (i = 0; i < FMTLEN; i++) {
            if (FMTCHR(i) == 'w')
                w++;
            else if (FMTCHR(i) == 'n')
                n++;
        }
        while (!done) {
            int wi = 0, ni = 0;
            alloc_445DB0(this, w, n);
            for (i = 0; i < FMTLEN; i++) {
                if (imp_006071E4(TOK, d_0060FA8B))
                    keyword_445DB0(d_0060A610, kw, file, 0x180);
                if (!field_445DB0(this, FMTCHR(i), &wi, &ni))
                    number_445DB0(file, kw, TOK, 0x18a);
                if (nl == 1) {
                    done = 1;
                    break;
                }
                sub_00445C60(this);
                if (this[4] == '\n')
                    nl = 1;
            }
            COUNT++;
        }
    }
    *out_tbl = this + 0x298;
    *out_n = COUNT;
    imp_00607330(kw);
    return 1;
}
