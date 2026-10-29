/* 0x004D3350: Lua talker method Select(speaker, script, style, choices): the speaker (argument 1) talks with the
 * "ConversationCamera" and "Talk" animation (0x0058B970) and gets the argument's ConversationCamera (0x0058B090); the
 * script (argument 2) becomes +0x168; the old choices (+0x140) are released; TextStyle[style.TextStyle] gives the
 * font size, and every text of the choices list (argument 3) becomes a text line (0x004B0290, size 0x254: x +0x180,
 * y from 0x00612174 going down by its lines * size + 4, ColorFile, Aligment, FontFile) kept in +0x140
 * (0x004D2C40); the talker waits for a choice (+0x7C = 2). Returns 0 */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4D3350;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_4D3350;                 /* nScript::Table */
typedef struct { void *tbl; Str_4D3350 key; } Ref_4D3350;
DECOMP_C void __thiscall sub_0046ACB0(void *self, Tbl_4D3350 *out);
DECOMP_C void __thiscall sub_0058B970(void *self, void *tbl, void *cam, void *anim);
DECOMP_C void *__thiscall sub_0046AAA0(void *self, Tbl_4D3350 *out, int i);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C void __thiscall sub_0058B090(void *self, void *cam);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_0047D060(void *first, void *last, void *dst, unsigned int a, unsigned int b,
                                   unsigned int c);
DECOMP_C void __cdecl sub_004E1BF0(void *eax, void *first, void *last, void *vec, unsigned int a);
DECOMP_C Str_4D3350 *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_4D3350 *__thiscall sub_0045C740(void *self, Ref_4D3350 *out, Str_4D3350 key);
DECOMP_C void *__thiscall sub_00464600(void *self, Tbl_4D3350 *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C int __cdecl sub_00402F40(unsigned int ebx, void *L, int idx);   /* lua_objlen */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C Str_4D3350 *__cdecl sub_00493100(unsigned int ebx, void *out);
DECOMP_C unsigned int *__thiscall sub_004B0290(void *self, float x, float y, float size, void *text, void *font,
                                               int align, int a, void *color, float scale, int b, int c);
DECOMP_C void __thiscall sub_004D2C40(void *self, void *p);
DECOMP_C char d_0061009C[], d_006120A0[], d_0061219C[], d_006110C0[], d_00612174[], d_008D122C[], d_0060C044[],
    d_00612190[], d_00612184[], d_00612178[], d_00609B68[], d_00607CB8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
typedef void (__thiscall *rel_4D3350)(void *self, int flag);

#define LS (*(void **)d_008D122C)
#define REG (-10000)

/* argument i of the Lua call as a table */
static void arg_4D3350(void *args, int i, Tbl_4D3350 *out)
{
    struct { void *a; int i; } ref;
    ref.a = args;
    ref.i = i;
    sub_0046ACB0(&ref, out);
}

/* string field key of the table t */
static Str_4D3350 *field_4D3350(Tbl_4D3350 *t, const char *key, unsigned int ebx, Str_4D3350 *out)
{
    struct { Tbl_4D3350 *t; const char *k; } ref;
    ref.t = t;
    ref.k = key;
    return sub_00463B40(&ref, ebx, out);
}

DECOMP(004D3350)
int __thiscall f_004D3350(char *this, void *args)
{
    Str_4D3350 anim, cam;
    Tbl_4D3350 t, t2, t3, style, choices;
    float size, y;
    struct { void *vt; void *child; unsigned char done; int i, n; } it;

    imp_00607324(&anim, d_0061009C);
    imp_00607324(&cam, d_006120A0);
    arg_4D3350(args, 1, &t);
    sub_0058B970(*(void **)(this + 0x174), &t, &cam, &anim);
    sub_004220A0(&t);
    imp_00607330(&cam);
    imp_00607330(&anim);

    sub_0058B090(*(void **)(this + 0x174), sub_0057B4E0(sub_0046AAA0(args, &t2, 1), &t3, d_006120A0));
    sub_004220A0(&t3);
    sub_004220A0(&t2);
    arg_4D3350(args, 2, &t);
    sub_0057A860(this + 0x168, &t);
    sub_004220A0(&t);

    {
        void **b = *(void ***)(this + 0x144), **e = *(void ***)(this + 0x148);
        if (b != e) {
            void *ne = sub_0047D060(e, e, b, 0, 0, 0);
            sub_004E1BF0(ne, ne, *(void **)(this + 0x148), this + 0x140, 0);
            *(void **)(this + 0x148) = ne;
        }
    }

    {
        Tbl_4D3350 a1, ts, st;
        Ref_4D3350 r;
        Str_4D3350 key;
        void *tbl = sub_0046AAA0(args, &a1, 1);
        struct { void *t; const char *k; } ref;
        ref.t = tbl;
        ref.k = d_0061219C;
        sub_00463B40(&ref, 0, &key);
        sub_00464600(sub_0045C740(sub_004323E0(&ts, d_0061219C), &r, key), &st);
        sub_00435D90(&style, &st);
        sub_004220A0(&st);
        imp_00607330(&r.key);
        sub_004220A0(&ts);
        sub_004220A0(&a1);
    }
    size = sub_0057AD40(&style, d_006110C0);
    arg_4D3350(args, 3, &t);
    sub_00435D90(&choices, &t);
    sub_004220A0(&t);

    y = *(float *)d_00612174;
    sub_00403390(LS, REG, choices.w[2]);
    it.child = 0;
    it.vt = d_0060C044;
    it.n = sub_00402F40(0, LS, -1);
    sub_00403390(LS, -1, 1);
    it.i = 1;
    it.done = it.n < 1;
    while (!it.done) {
        void *mem = sub_005E3EAE(0x254);
        unsigned int *line = 0;
        if (mem) {
            Str_4D3350 color, align, font, text;
            Str_4D3350 *pc = field_4D3350(&style, d_00612190, 0, &color);
            Str_4D3350 *pa = field_4D3350(&style, d_00612184, 1, &align);
            Str_4D3350 *pf = field_4D3350(&style, d_00612178, 3, &font);
            Str_4D3350 *pt = sub_00493100(7, &text);
            unsigned char al = *imp_00607208(pa, 0);
            line = sub_004B0290(mem, *(float *)(this + 0x180), y, size, pt, pf, al, 1, pc, 1.0f, 0, 0);
            if (line)
                line[1]++;
            sub_004D2C40(this + 0x140, &line);
            if (line && --line[1] == 0)
                ((rel_4D3350)(*(void ***)line)[0])(line, 1);
            imp_00607330(&text);
            imp_00607330(&font);
            imp_00607330(&align);
            imp_00607330(&color);
        } else {
            sub_004D2C40(this + 0x140, &line);
        }
        {
            char *last = *(char **)(*(char **)(this + 0x148) - 4);
            float d = (float)(*(int *)(last + 0x24c) * (long double)size + y);
            y = (float)(d + *(double *)d_00609B68);
        }
        sub_00402A70(LS, -2);
        it.i++;
        sub_00403390(LS, -1, it.i);
        it.done = it.i > it.n;
    }
    it.vt = d_0060C044;
    sub_00402A70(LS, -3);
    it.vt = d_00607CB8;
    sub_00422000(&it);
    *(int *)(this + 0x7c) = 2;
    sub_004220A0(&choices);
    sub_004220A0(&style);
    return 0;
}
