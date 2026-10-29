/* 0x00447A50: CEffect::CEffect(name): the effect file name + ".ef" (or ".fx") is read (0x00459200 / 0x00459050) and
 * compiled (D3DXCreateEffect into +0x20); a failure to open or compile throws (0x00421220 with ".\Effect.cpp" lines
 * 0x33 / 0x6B, the compiler's message added); compiler warnings go to the log (0x006C8978 with the time of
 * 0x004F6660); the first valid technique is set (or it throws, line 0x7B); every "texture" token of the source (up
 * to "technique") names a string parameter "s..." whose texture (0x004DF920, size 0x54) is set to "t..." and kept with
 * its handle (+0x24 array of 0x40 pairs); the textures are copied to the +0x30 array (0x0042B1F0, 0x004477F0) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_447A50;                 /* std::string */
typedef struct { unsigned int w[0x30 / 4]; } Exc_447A50;
typedef struct { unsigned int w[0x30 / 4]; } File_447A50;
DECOMP_C void __thiscall sub_00459200(void *self);
DECOMP_C unsigned char __thiscall sub_00459050(void *self, void *name, int mode);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C long __stdcall sub_005B807A(void *dev, const void *src, unsigned int len, void *defs, void *inc,
                                     unsigned int flags, void *pool, void **eff, void **errs);   /* D3DXCreateEffect */
DECOMP_C void *__cdecl sub_004F6660(void *out);
DECOMP_C void *__cdecl sub_00447860(void *os, const char *s);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                        /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                                   /* operator delete[] */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int a);
DECOMP_C void __thiscall sub_00459010(void *self);
DECOMP_C void __thiscall sub_0042B1F0(void *self, unsigned int n);
DECOMP_C void **__thiscall sub_004477F0(void *self, unsigned int i);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C char d_0060A84C[], d_0060A744[], d_006C8C10[], d_0060A840[], d_00608E98[], d_0060A81C[], d_0060A80C[],
    d_0069916C[], d_0060A7E4[], d_0060A7CC[], d_0060A7B8[], d_0060A7A0[], d_0060A79C[], d_006C8978[], d_0060A76C[],
    d_0060A764[], d_0060A758[], d_0060A750[];
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071D8)(void *, const char *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBDABV10@@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *imp_006072C0 __asm__("__imp_?endl@std@@YAAAV?$basic_ostream@DU?$char_traits@D@std@@@1@AAV21@@Z");
DECOMP_C void *(__cdecl *imp_006072BC)(void *, const void *) __asm__("__imp_??$?6DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YAAAV?$basic_ostream@DU?$char_traits@D@std@@@0@AAV10@ABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@@Z");
DECOMP_C void *(__thiscall *imp_006072B8)(void *, void *) __asm__("__imp_??6?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV01@P6AAAV01@AAV01@@Z@Z");
DECOMP_C void *(__cdecl *imp_00607408)(unsigned int) __asm__("__imp__malloc");
DECOMP_C char *(__cdecl *imp_006073CC)(char *, const char *) __asm__("__imp__strtok");
DECOMP_C char *(__cdecl *imp_00607414)(char *) __asm__("__imp___strlwr");
typedef long (__stdcall *dev3_447A50)(void *dev, int a, int b);
typedef const char *(__stdcall *bufp_447A50)(void *buf);
typedef unsigned long (__stdcall *rel_447A50)(void *buf);
typedef long (__stdcall *find_447A50)(void *eff, void *from, void **tech);
typedef long (__stdcall *set_447A50)(void *eff, void *tech);
typedef long (__stdcall *gets_447A50)(void *eff, const char *name, const char **out);
typedef long (__stdcall *sett_447A50)(void *eff, const char *name, void *tex);
typedef void *(__stdcall *getp_447A50)(void *eff, void *parent, const char *name);
typedef void *(__thiscall *tex_447A50)(void *self);

#define VT(o) (*(void ***)(o))

static void throw_447A50(void *msg, int line)
{
    Exc_447A50 e;
    sub_00421220(&e, msg, d_0060A80C, line);
    sub_005E3EC0(&e, d_0069916C);
}

/* repe cmpsb over n bytes */
static int same_447A50(const char *a, const char *b, int n)
{
    while (n--)
        if (*a++ != *b++)
            return 0;
    return 1;
}

DECOMP(00447A50)
void *__thiscall f_00447A50(char *this, void *name)
{
    void *errs = 0, *tech, *dev;
    unsigned int *arr = (unsigned int *)(this + 0x24);
    File_447A50 f;
    Str_447A50 s, t1, t2, t3, ts;
    unsigned char ok;
    char *buf, *tok;
    unsigned int n, i;

    *(void **)this = d_0060A84C;
    imp_006071E0(this + 4);
    arr[0] = 0;
    arr[1] = 0;
    arr[2] = 0x40;
    arr[0] = (unsigned int)(size_t)imp_00607408(0x200);
    *(void **)(this + 0x30) = d_0060A744;
    *(int *)(this + 0x34) = 0;
    *(int *)(this + 0x38) = 0;
    imp_0060731C(this + 4, name);
    *(void **)(this + 0x20) = 0;
    dev = *(void **)d_006C8C10;
    ((dev3_447A50)VT(dev)[0x104 / 4])(dev, 0, 0);
    sub_00459200(&f);

    ok = sub_00459050(&f, imp_006071DC(&s, this + 4, d_0060A840), 0);
    imp_00607330(&s);
    if (!ok) {
        ok = sub_00459050(&f, imp_006071DC(&s, this + 4, d_00608E98), 0);
        imp_00607330(&s);
        if (!ok)
            throw_447A50(imp_006071D8(&t1, d_0060A81C, this + 4), 0x33);
    }

    if (sub_005B807A(*(void **)d_006C8C10, (const void *)(size_t)f.w[0x28 / 4], *(unsigned int *)(f.w[0x24 / 4] + 8),
                     0, 0, 0, 0, (void **)(this + 0x20), &errs) < 0) {
        imp_006071E0(&s);
        if (errs) {
            imp_006072F8(&s, ((bufp_447A50)VT(errs)[0xc / 4])(errs));
            if (errs) {
                ((rel_447A50)VT(errs)[8 / 4])(errs);
                errs = 0;
            }
        }
        throw_447A50(imp_006071C0(&t3, imp_006071DC(&t2, imp_006071D8(&t1, d_0060A7E4, this + 4), d_0060A7CC), &s),
                     0x6b);
    }
    if (errs) {
        imp_00607324(&s, ((bufp_447A50)VT(errs)[0xc / 4])(errs));
        if (s.w[5]) {
            void *msg = imp_006071C0(&t3, imp_006071DC(&t2, imp_006071D8(&t1, d_0060A7B8, this + 4), d_0060A7A0), &s);
            void *os = imp_006072BC(sub_00447860(imp_006072BC(d_006C8978, sub_004F6660(&ts)), d_0060A79C), msg);
            imp_006072B8(os, imp_006072C0);
            imp_00607330(&ts);
            imp_00607330(&t3);
            imp_00607330(&t2);
            imp_00607330(&t1);
        }
        imp_00607330(&s);
        if (errs) {
            ((rel_447A50)VT(errs)[8 / 4])(errs);
            errs = 0;
        }
    }

    {
        void *eff = *(void **)(this + 0x20);
        if (((find_447A50)VT(eff)[0xf4 / 4])(eff, 0, &tech) < 0)
            throw_447A50(imp_006071D8(&t2, d_0060A76C, this + 4), 0x7b);
        eff = *(void **)(this + 0x20);
        ((set_447A50)VT(eff)[0xe8 / 4])(eff, tech);
    }

    buf = sub_005E3B10(*(unsigned int *)(f.w[0x24 / 4] + 8) + 1);
    __builtin_strcpy(buf, (const char *)(size_t)f.w[0x28 / 4]);
    tok = imp_006073CC(buf, d_0060A764);
    imp_00607414(tok);
    arr[1] = 0;
    if (!same_447A50(tok, d_0060A758, 10) && tok) {
        do {
            if (same_447A50(tok, d_0060A758, 10))
                break;
            if (same_447A50(tok, d_0060A750, 8)) {
                const char *path;
                char *pn = imp_006073CC(0, d_0060A764);
                void *eff = *(void **)(this + 0x20);
                pn[0] = 's';
                if (((gets_447A50)VT(eff)[0xcc / 4])(eff, pn, &path) >= 0) {
                    void *mem = sub_005E3EAE(0x54), *tex = 0, *h;
                    if (mem) {
                        imp_00607324(&s, path);
                        tex = sub_004DF920(mem, &s, 0);
                        imp_00607330(&s);
                    }
                    pn[0] = 't';
                    eff = *(void **)(this + 0x20);
                    ((sett_447A50)VT(eff)[0xd0 / 4])(eff, pn, ((tex_447A50)VT(tex)[0x28 / 4])(tex));
                    eff = *(void **)(this + 0x20);
                    h = ((getp_447A50)VT(eff)[0x24 / 4])(eff, 0, pn);
                    if (arr[1] < arr[2]) {
                        ((void **)(size_t)arr[0])[arr[1] * 2] = h;
                        ((void **)(size_t)arr[0])[arr[1] * 2 + 1] = tex;
                        arr[1]++;
                    }
                }
            }
            tok = imp_006073CC(0, d_0060A764);
            imp_00607414(tok);
        } while (tok);
    }
    sub_005E3EBA(buf);
    sub_00459010(&f);

    n = arr[1];
    if (n) {
        char *a = this + 0x30;
        sub_0042B1F0(a, n);
        for (i = 0; i < n; i++) {
            void **e = sub_004477F0(arr, i);
            (*(void ***)(a + 4))[(*(unsigned int *)(a + 8))++] = e[1];
        }
    }
    sub_00459170(&f);
    return this;
}
