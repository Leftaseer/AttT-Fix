/* 0x005A9550: the map editor dialog's GUI event handler (event, control id, control; the dialog is the control's
 * +0x18, the editor 0x006C88D8): the tool buttons toggle the editor mode (+0x9C; "Click" and red while on, "Add"
 * and yellow when off), the paint radio groups (0x008D1308 / 0x008D130C / 0x008D1318), the object choices pick the
 * group's lists (NPC, SAO, TREES, SKMS / Unit animations, PSPS, a model group without its gizmos) and fill the
 * combo boxes (sorted by 0x005A8390), the object names set the selected object's parts, the animation list edits
 * "unit, animation, speed" rows and writes them to the object's Anim table; on 0x601 (slider moved) the sliders set
 * the editor's brush values (0x005B1C10..) and the effect sizes */
/* @conv - 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5A9550;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_5A9550;                 /* nScript::Table */
typedef struct { unsigned int w[4]; } Vec_5A9550;                 /* std::vector<std::string> */
typedef struct { void *tbl; Str_5A9550 key; } Ref_5A9550;
typedef struct { Tbl_5A9550 t; const char *k; } RefC_5A9550;
DECOMP_C void __thiscall sub_00593E00(void *self, unsigned int color, unsigned int color2, int a);
DECOMP_C char *__thiscall sub_00594600(void *self, int id, int a);
DECOMP_C void *__thiscall sub_00594ED0(void *self);
DECOMP_C const char *__thiscall sub_00594EF0(void *self);
DECOMP_C void __thiscall sub_00594F80(void *self, int a);
DECOMP_C void __thiscall sub_00594FD0(void *self, const char *text);
DECOMP_C int __thiscall sub_00595630(void *self, int a);
DECOMP_C void __thiscall sub_00596EE0(void *self, const char *text);
DECOMP_C void __thiscall sub_00597290(void *self, const char *text, int a);
DECOMP_C void __thiscall sub_005977C0(void *self, const char *text, int a);
DECOMP_C const char *__thiscall sub_00597900(void *self, int i);
DECOMP_C void __thiscall sub_00598080(void *self, const char *text, int a);
DECOMP_C void __thiscall sub_00598520(void *self);
DECOMP_C void __thiscall sub_005985E0(void *self);
DECOMP_C void __thiscall sub_005A1350(void *self, float v);
DECOMP_C char *__thiscall sub_005A1790(void *self, int i);
DECOMP_C void __thiscall sub_005A2410(void *self, int a, int b);
DECOMP_C void __thiscall sub_005A25B0(void *self, int a, int b);
DECOMP_C void __thiscall sub_005A8A30(void *self);
DECOMP_C void __thiscall sub_005AC4A0(void *self, void *name);
DECOMP_C void __cdecl sub_005ACE90(void *self, unsigned int ebx, void *a, Str_5A9550 b, void *c, void *d);
DECOMP_C void __thiscall sub_005AD210(void *self, void *obj);
DECOMP_C void __thiscall sub_005B1C10(void *self, float v);
DECOMP_C void __thiscall sub_005B1C60(void *self, float v);
DECOMP_C void __thiscall sub_005B1CB0(void *self, float v);
DECOMP_C void __thiscall sub_005B1D00(void *self, float v);
DECOMP_C void __thiscall sub_005B1D50(void *self, float v);
DECOMP_C void __thiscall sub_005B1DA0(void *self, float v);
DECOMP_C void __thiscall sub_005B1DF0(void *self, float v);
DECOMP_C void __thiscall sub_005B1E40(void *self, float v);
DECOMP_C void __thiscall sub_005B1E90(void *self, float v);
DECOMP_C void *__thiscall sub_0058F290(void *self);
DECOMP_C void __thiscall sub_0045E430(void *self, int a);
DECOMP_C int __thiscall sub_0045CA40(void *self, void *part);
DECOMP_C void __thiscall sub_0045D330(void *self, void *part);
DECOMP_C Vec_5A9550 *__thiscall sub_00579920(void *self, void *name);
DECOMP_C void __thiscall sub_00434AB0(void *self, const void *s);
DECOMP_C void __cdecl sub_00434A60(void *self, unsigned int eax);
DECOMP_C void *__cdecl sub_005A1F40(void *out, void *first, void *last, const void *val);
DECOMP_C void __cdecl sub_005A8390(void *first, void *last);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C int __thiscall sub_0045BCF0(void *self);
DECOMP_C void __thiscall sub_0045C870(void *self, int ref);
DECOMP_C void __thiscall sub_0045B580(void *self);
DECOMP_C void __thiscall sub_0045C920(void *self);
DECOMP_C Str_5A9550 *__cdecl sub_0047CE00(unsigned int ebx, Str_5A9550 *out);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void *__thiscall sub_00435E00(void *self, int a);
DECOMP_C Ref_5A9550 *__thiscall sub_0045C740(void *self, Ref_5A9550 *out, Str_5A9550 key);
DECOMP_C RefC_5A9550 *__thiscall sub_004648E0(void *self, RefC_5A9550 *out, const char *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C void __thiscall sub_0045BAC0(void *self, const void *s);
DECOMP_C void __thiscall sub_00531F80(void *self, float v);
DECOMP_C void __thiscall sub_0057BEA0(void *t, int i, void *v);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, void *val);
DECOMP_C void __thiscall sub_00537B70(void *self);
DECOMP_C char *__cdecl sub_00518B10(void);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C void __cdecl sub_0054D350(void *self, int eax, float rate);
DECOMP_C const char *__cdecl sub_00592C30(const void *wtext);
DECOMP_C char d_006C88D8[], d_008D1308[], d_008D130C[], d_008D1318[], d_0060C9F0[], d_006898AC[], d_00620614[],
    d_00620770[], d_00620780[], d_0060B940[], d_006100BC[], d_006107E8[], d_00620750[], d_00615C14[], d_0061B5C8[],
    d_006207C8[], d_006207B8[], d_006207A8[], d_0062078C[], d_0062075C[], d_00612630[], d_0060B918[], d_00615C0C[],
    d_0062066C[], d_006207D8[], d_0060C088[], d_0060C138[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void *(__thiscall *imp_00607320)(void *, const char *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_006071FC)(void *, const void *) __asm__("__imp_??Y?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C unsigned int (__thiscall *imp_006071BC)(const void *, const char *, unsigned int) __asm__("__imp_?find@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIPBDI@Z");
DECOMP_C unsigned int (__thiscall *imp_006072E0)(const void *, char, unsigned int) __asm__("__imp_?find@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIDI@Z");
DECOMP_C unsigned int (__thiscall *imp_006071C8)(const void *, char, unsigned int) __asm__("__imp_?rfind@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEIDI@Z");
DECOMP_C void *(__thiscall *imp_006071CC)(const void *, void *, unsigned int, unsigned int) __asm__("__imp_?substr@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBE?AV12@II@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C unsigned int *imp_npos __asm__("__imp_?npos@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@2IB");
DECOMP_C double (__cdecl *imp_atof)(const char *) __asm__("__imp__atof");
DECOMP_C int (__cdecl *imp_sprintf)(char *, const char *, ...) __asm__("__imp__sprintf");
DECOMP_C void __stdcall f_005A9550(unsigned int event, int id, void *control);
typedef void (__thiscall *vf54_5A9550)(void *self, int a, int b, int c);
typedef void (__thiscall *vf2c_5A9550)(void *self, void *name, int a);
typedef void (__thiscall *slider_5A9550)(void *self, float v);

#define ED (*(char **)d_006C88D8)
#define NPOS (*imp_npos)
#define PAINT (*(int *)d_008D1308)
#define PAINT_A ((int *)d_008D130C)
#define PAINT_B ((int *)d_008D1318)

/* the control's text as a string */
static void text_5A9550(Str_5A9550 *s, void *ctrl)
{
    imp_00607324(s, sub_00594EF0(ctrl));
}

/* s cut before its last '.' */
static void stem_5A9550(Str_5A9550 *s)
{
    Str_5A9550 t;
    imp_006071CC(s, &t, 0, imp_006071C8(s, '.', NPOS));
    imp_0060731C(s, &t);
    imp_00607330(&t);
}

/* the slider's value (its +0x54 text) */
static float value_5A9550(char *ctrl)
{
    return (float)imp_atof(sub_00592C30(*(void **)(ctrl + 0x54)));
}

/* a tool button: mode on (red, "Click") or off (yellow, "Add") */
static void tool_5A9550(char *dlg, int id, int mode, const unsigned int *off, const unsigned int *on)
{
    if (*(int *)(ED + 0x9c) == mode) {
        sub_00596EE0(sub_00594600(dlg, id, 0), d_0062066C);
        __builtin_memcpy(**(char ***)(sub_00594600(dlg, id, 0) + 0x20) + 0x44, off, 40);
        *(int *)(ED + 0x9c) = 0;
    } else {
        sub_00596EE0(sub_00594600(dlg, id, 0), d_006207D8);
        __builtin_memcpy(**(char ***)(sub_00594600(dlg, id, 0) + 0x20) + 0x44, on, 40);
        *(int *)(ED + 0x9c) = mode;
    }
}

/* a paint radio group: the buttons of the group and of its choice pressed */
static void paint_5A9550(char *ctrl, int group, int pressed)
{
    char *b;
    PAINT = group;
    b = sub_00594600(*(void **)(ctrl + 0x18), pressed, 3);
    ((vf54_5A9550)(*(void ***)b)[0x54 / 4])(b, 1, 1, 0);
    b = sub_00594600(*(void **)(ctrl + 0x18), PAINT_A[PAINT], 3);
    ((vf54_5A9550)(*(void ***)b)[0x54 / 4])(b, 1, 1, 0);
}

/* the keys of the Lua table t pushed into v */
static void keys_5A9550(Vec_5A9550 *v, Tbl_5A9550 *t)
{
    unsigned int it[4];
    sub_0045C870(it, sub_0045BCF0(t));
    while (!*(unsigned char *)&it[2]) {
        Str_5A9550 k;
        sub_00434AB0(v, sub_0047CE00(0, &k));
        imp_00607330(&k);
        sub_0045B580(it);
    }
    sub_0045C920(it);
}

/* v sorted and added to the combo box */
static void fill_5A9550(char *combo, Vec_5A9550 *v, const char *head)
{
    Str_5A9550 *e = (Str_5A9550 *)(size_t)v->w[1], *end = (Str_5A9550 *)(size_t)v->w[2];
    sub_005A8390(e, end);
    if (head)
        sub_00597290(combo, head, 0);
    for (; e != end; e++)
        sub_00597290(combo, imp_0060732C(e), 0);
}

/* the "unit, animation, speed" row of the animation editor */
static void row_5A9550(char *dlg, Str_5A9550 *row, Str_5A9550 *anim)
{
    Str_5A9550 unit, t;
    char buf[32];
    text_5A9550(&unit, sub_00594600(dlg, 0x190, 4));
    imp_006071DC(&t, &unit, d_00612630);
    imp_006071C0(row, &t, anim);
    imp_00607330(&t);
    imp_00607320(row, d_00612630);
    imp_sprintf(buf, d_0060B918, (double)value_5A9550(sub_00594600(dlg, 0x1a1, 6)));
    imp_00607320(row, buf);
    imp_00607330(&unit);
}

/* the object group choice (0x1B6) */
static void group_5A9550(char *dlg, char *ctrl)
{
    Str_5A9550 s;
    text_5A9550(&s, ctrl);
    if (imp_006071E4(&s, d_0060B940)) {
        sub_005A25B0(dlg, 5, 0);
    } else if (imp_006071E4(&s, d_006100BC) || imp_006071E4(&s, d_006107E8)) {
        int npc = imp_006071E4(&s, d_006100BC);
        char *combo;
        Tbl_5A9550 t;
        Vec_5A9550 v;
        sub_005A25B0(dlg, npc ? 9 : 0xb, 1);
        combo = sub_00594600(dlg, npc ? 0x183 : 0x1dc, 4);
        sub_00598520(combo);
        sub_004323E0(&t, npc ? d_006100BC : d_006107E8);
        v.w[1] = v.w[2] = v.w[3] = 0;
        keys_5A9550(&v, &t);
        fill_5A9550(combo, &v, npc ? d_006207C8 : d_006207B8);
        sub_00434A60(&v, 0);
        sub_004220A0(&t);
    } else if (imp_006071E4(&s, d_00620750)) {
        char *combo, *trees, *e;
        Vec_5A9550 v;
        sub_005A25B0(dlg, 8, 1);
        combo = sub_00594600(dlg, 0x178, 4);
        sub_00598520(combo);
        trees = **(char ***)(sub_00518B10() + 0xd4);
        v.w[1] = v.w[2] = v.w[3] = 0;
        for (e = *(char **)(trees + 0x28); e != *(char **)(trees + 0x2c); e += 0x30)
            sub_00434AB0(&v, e);
        fill_5A9550(combo, &v, d_006207A8);
        sub_00434A60(&v, 0);
    } else if (imp_006071E4(&s, d_00615C14)) {
        char *combo;
        Tbl_5A9550 t;
        Vec_5A9550 v;
        sub_005A25B0(dlg, 0xa, 1);
        combo = sub_00594600(dlg, 0x190, 4);
        sub_00598520(combo);
        sub_005985E0(sub_00594600(dlg, 0x1c2, 8));
        sub_00597290(combo, d_0062078C, 0);
        v.w[1] = v.w[2] = v.w[3] = 0;
        sub_004323E0(&t, d_0060C088);
        keys_5A9550(&v, &t);
        fill_5A9550(combo, &v, 0);
        sub_004220A0(&t);
        sub_00434A60(&v, 0);
    } else if (imp_006071E4(&s, d_0061B5C8)) {
        sub_005A25B0(dlg, 7, 1);
    } else {
        Vec_5A9550 *l;
        char *combo;
        Str_5A9550 *e;
        unsigned char found = 0;
        sub_005A25B0(dlg, 5, 1);
        l = sub_00579920(dlg + 0x244, &s);
        combo = sub_00594600(dlg, 0x151, 4);
        sub_00598520(combo);
        for (e = (Str_5A9550 *)(size_t)l->w[1]; e != (Str_5A9550 *)(size_t)l->w[2]; e++)
            if (imp_006071BC(e, d_00620614, 0) == NPOS) {
                sub_00597290(combo, imp_0060732C(e), 0);
                found = 1;
            }
        if (found)
            f_005A9550(0, 0x151, combo);
        else {
            sub_005A25B0(dlg, 5, 0);
            sub_00594FD0(ctrl, d_0060B940);
        }
    }
    imp_00607330(&s);
}

/* the object model choice (0x151): its gizmo model offered */
static void model_5A9550(char *dlg, char *ctrl)
{
    Str_5A9550 s, g, t, grp;
    Vec_5A9550 *l;
    char *combo;
    Str_5A9550 *e;
    void *found;
    text_5A9550(&s, ctrl);
    imp_006071CC(&s, &g, 0, imp_006071C8(&s, '.', NPOS));
    imp_00607320(&g, d_00620614);
    imp_006071CC(&s, &t, imp_006071C8(&s, '.', NPOS), NPOS);
    imp_006071FC(&g, &t);
    imp_00607330(&t);
    text_5A9550(&grp, sub_00594600(dlg, 0x1b6, 4));
    l = sub_00579920(dlg + 0x244, &grp);
    imp_00607330(&grp);
    combo = sub_00594600(dlg, 0x165, 4);
    sub_00598520(combo);
    sub_00597290(combo, d_006898AC, 0);
    for (e = (Str_5A9550 *)(size_t)l->w[1]; e != (Str_5A9550 *)(size_t)l->w[2]; e++)
        if (imp_006071BC(e, d_00620614, 0) != NPOS)
            sub_00597290(combo, imp_0060732C(e), 0);
    sub_00594FD0(sub_00594600(dlg, 0x154, 4), d_00620770);
    sub_005A1F40(&found, (void *)(size_t)l->w[1], (void *)(size_t)l->w[2], &g);
    if (found == (void *)(size_t)l->w[2]) {
        sub_00594F80(combo, 0);
        sub_005A2410(dlg, 6, 0);
    } else {
        sub_00594FD0(sub_00594600(dlg, 0x167, 4), d_00620770);
        sub_00594FD0(combo, imp_0060732C(&g));
        sub_005A2410(dlg, 6, 1);
    }
    imp_00607330(&g);
    imp_00607330(&s);
}

/* the animations of the chosen unit (0x190) */
static void unit_5A9550(char *dlg, char *ctrl)
{
    char *combo = sub_00594600(dlg, 0x1c3, 4);
    Str_5A9550 s;
    text_5A9550(&s, ctrl);
    sub_00598520(combo);
    sub_005985E0(sub_00594600(dlg, 0x1c2, 8));
    if (imp_00607214(&s, d_0062078C)) {
        Vec_5A9550 v;
        Tbl_5A9550 anim;
        sub_00597290(combo, d_0062075C, 0);
        v.w[1] = v.w[2] = v.w[3] = 0;
        {
            Str_5A9550 k;
            Tbl_5A9550 h, tmp;
            Ref_5A9550 r;
            RefC_5A9550 rc;
            imp_00607334(&k, &s);
            sub_0044C0E0(sub_004648E0(sub_0045C740(sub_004323E0(&h, d_0060C088), &r, k), &rc, d_0060C138), &tmp);
            sub_00435D90(&anim, &tmp);
            sub_004220A0(&tmp);
            sub_004220A0(&rc.t);
            imp_00607330(&r.key);
            sub_004220A0(&h);
        }
        keys_5A9550(&v, &anim);
        fill_5A9550(combo, &v, 0);
        sub_00598080(sub_00594600(dlg, 0x1a1, 6), d_0060C9F0, 0);
        sub_004220A0(&anim);
        sub_00434A60(&v, 0);
    }
    imp_00607330(&s);
}

/* the animation rows written to the selected object's Anim table (0x1CB) */
static void anims_5A9550(char *dlg, char *ctrl)
{
    Str_5A9550 s;
    char *g;
    text_5A9550(&s, sub_00594600(dlg, 0x190, 4));
    g = *(char **)(ED + 0x68);
    if (g && *(int *)(g + 0x354) == 6) {
        char *obj = *(char **)(g + 0x1bc), *lst;
        Tbl_5A9550 anim, row, t;
        struct { void *t; int i; } r1, r2, r3;
        int i;
        sub_00435E00(&anim, 0);
        lst = sub_00594600(dlg, 0x1c2, 8);
        r1.t = &row;
        r1.i = 1;
        r2.t = &row;
        r2.i = 2;
        r3.t = &row;
        r3.i = 3;
        for (i = 0; i < *(int *)(lst + 0x150);) {
            Str_5A9550 a;
            unsigned int p, q;
            sub_00435E00(&row, 0);
            imp_006072F8(&s, sub_00597900(lst, i));
            p = imp_006072E0(&s, ',', 0);
            sub_0045BAC0(&r1, imp_006071CC(&s, &a, 0, p));
            imp_00607330(&a);
            q = imp_006072E0(&s, ',', p + 2);
            sub_0045BAC0(&r2, imp_006071CC(&s, &a, p + 2, q - p - 2));
            imp_00607330(&a);
            imp_006071CC(&s, &a, imp_006071C8(&s, ',', NPOS) + 2, NPOS);
            sub_00531F80(&r3, (float)imp_atof(imp_0060732C(&a)));
            imp_00607330(&a);
            i++;
            sub_0057BEA0(&anim, i, &row);
            sub_004220A0(&row);
        }
        sub_00435D90(&t, obj + 0x1e8);
        sub_0057BF50(&t, d_00615C0C, &anim);
        sub_00537B70(obj);
        sub_004220A0(&t);
        sub_004220A0(&anim);
    }
    imp_00607330(&s);
    (void)ctrl;
}

DECOMP(005A9550)
void __stdcall f_005A9550(unsigned int event, int id, void *control)
{
    char *ctrl = (char *)control, *dlg = *(char **)(ctrl + 0x18);
    unsigned int off[16], on[16];

    sub_00593E00(off, 0xffffff00u, 0xc8808080u, 0);
    sub_00593E00(on, 0xffff0000u, 0xc8808080u, 0);
    switch (id) {
    case 0x13f:
    case 0x1ce:
    case 0x140: {
        void *o = sub_00594ED0(sub_00594600(dlg, id, 4));
        if (o)
            sub_005AD210(ED, o);
        else
            sub_005A2410(dlg, id == 0x140 ? 3 : 1, 0);
        break;
    }
    case 0x141:
    case 0x144:
    case 0x142:
    case 0x145:
    case 0x143:
    case 0x146:
    case 0x147:
    case 0x148:
    case 0x1b9:
    case 0x1bb: {
        float v;
        if (event != 0x601)
            return;
        v = value_5A9550(ctrl);
        switch (id) {
        case 0x141:
        case 0x144:
            sub_005B1C10(ED, v);
            break;
        case 0x142:
        case 0x145:
            sub_005B1C60(ED, v);
            break;
        case 0x143:
        case 0x146:
            sub_005B1CB0(ED, v);
            break;
        case 0x147:
        case 0x148:
            sub_005B1D50(ED, v);
            break;
        default:
            sub_005B1DF0(ED, v);
            break;
        }
        return;
    }
    case 0x149:
        paint_5A9550(ctrl, 0, PAINT_B[0]);
        break;
    case 0x14a:
        paint_5A9550(ctrl, 1, PAINT_B[1]);
        break;
    case 0x14b:
        paint_5A9550(ctrl, 2, PAINT_B[2]);
        break;
    case 0x14c:
    case 0x14d:
        PAINT_B[PAINT] = id;
        break;
    case 0x1b1:
    case 0x1b2:
    case 0x1b3:
        PAINT_A[PAINT] = id;
        break;
    case 0x151:
        model_5A9550(dlg, ctrl);
        break;
    case 0x156: {
        char *g = *(char **)(ED + 0x68);
        if (*(int *)(g + 0x354) == 0)
            sub_0045E430(sub_0058F290(g), (unsigned char)ctrl[0x15c]);
        break;
    }
    case 0x157: {
        char *g = *(char **)(ED + 0x68);
        if (g && *(int *)(g + 0x354) == 0) {
            Str_5A9550 s;
            text_5A9550(&s, ctrl);
            sub_0045CA40(sub_0058F290(g), &s);
            imp_00607330(&s);
            sub_005AD210(ED, *(void **)(g + 0x1bc));
        }
        break;
    }
    case 0x1bd: {
        char *g = *(char **)(ED + 0x68);
        if (g && *(int *)(g + 0x354) == 0) {
            Str_5A9550 s;
            text_5A9550(&s, ctrl);
            sub_0045D330(sub_0058F290(g), &s);
            sub_005AD210(ED, *(void **)(g + 0x1bc));
            imp_00607330(&s);
        }
        break;
    }
    case 0x165: {
        Str_5A9550 s;
        text_5A9550(&s, ctrl);
        sub_005A2410(dlg, 6, imp_006071E4(&s, d_006898AC) ? 0 : 1);
        imp_00607330(&s);
        break;
    }
    case 0x183:
        sub_00594FD0(sub_00594600(dlg, 0x18a, 4), d_00620780);
        break;
    case 0x1dc:
        sub_00594FD0(sub_00594600(dlg, 0x1e3, 4), d_00620780);
        break;
    case 0x18a:
    case 0x1e3: {
        Str_5A9550 s;
        char *o;
        text_5A9550(&s, ctrl);
        stem_5A9550(&s);
        o = *(char **)(*(char **)(ED + 0x68) + 0x1bc);
        ((vf2c_5A9550)(*(void ***)o)[0x2c / 4])(o, &s, 0);
        imp_00607330(&s);
        break;
    }
    case 0x190:
        unit_5A9550(dlg, ctrl);
        break;
    case 0x1b4:
        tool_5A9550(dlg, 0x1b4, 1, off, on);
        break;
    case 0x1b5:
        tool_5A9550(dlg, 0x1b5, 2, off, on);
        break;
    case 0x1b7:
        tool_5A9550(dlg, 0x1b7, 3, off, on);
        break;
    case 0x1c0:
        tool_5A9550(dlg, 0x1c0, 4, off, on);
        break;
    case 0x1e4:
        tool_5A9550(dlg, 0x1e4, 5, off, on);
        break;
    case 0x1c1:
        tool_5A9550(dlg, 0x1c1, 6, off, on);
        break;
    case 0x1c5:
        tool_5A9550(dlg, 0x1c5, 7, off, on);
        break;
    case 0x1c6:
        tool_5A9550(dlg, 0x1c6, 8, off, on);
        break;
    case 0x1cf:
        tool_5A9550(dlg, 0x1cf, 9, off, on);
        break;
    case 0x1b6:
        group_5A9550(dlg, ctrl);
        break;
    case 0x1bc:
        sub_005A8A30(dlg);
        break;
    case 0x1c2: {
        char *lst = sub_00594600(dlg, 0x1c2, 8);
        if (sub_00595630(lst, -1) >= 0) {
            Str_5A9550 s, anim, speed;
            unsigned int p, q;
            imp_00607324(&s, sub_005A1790(sub_00594600(dlg, 0x1c2, 8), -1));
            p = imp_006072E0(&s, ',', 0);
            q = imp_006072E0(&s, ',', p + 2);
            imp_006071CC(&s, &anim, p + 2, q - p - 2);
            imp_006071CC(&s, &speed, imp_006071C8(&s, ',', NPOS) + 2, NPOS);
            sub_00594FD0(sub_00594600(dlg, 0x1c3, 4), imp_0060732C(&anim));
            {
                char *sl = sub_00594600(dlg, 0x1a1, 6);
                sub_00598080(sl, imp_0060732C(&speed), 0);
            }
            imp_00607330(&speed);
            imp_00607330(&anim);
            imp_00607330(&s);
        }
        break;
    }
    case 0x1c4: {
        char *combo = sub_00594600(dlg, 0x1c3, 4);
        if (*(unsigned int *)(combo + 0x26c)) {
            Str_5A9550 a;
            text_5A9550(&a, combo);
            if (imp_00607214(&a, d_0062075C)) {
                Str_5A9550 row;
                char *lst;
                row_5A9550(dlg, &row, &a);
                lst = sub_00594600(dlg, 0x1c2, 8);
                sub_005977C0(lst, imp_0060732C(&row), 0);
                imp_00607330(&row);
            }
            imp_00607330(&a);
        }
        break;
    }
    case 0x1ca: {
        if (sub_00595630(sub_00594600(dlg, 0x1c2, 8), -1) >= 0) {
            Str_5A9550 a, row;
            char *dst;
            const char *src;
            text_5A9550(&a, sub_00594600(dlg, 0x1c3, 4));
            row_5A9550(dlg, &row, &a);
            dst = sub_005A1790(sub_00594600(dlg, 0x1c2, 8), -1);
            src = imp_0060732C(&row);
            while ((*dst++ = *src++) != 0)
                ;
            imp_00607330(&row);
            imp_00607330(&a);
        }
        break;
    }
    case 0x1c8:
    case 0x1c9: {
        Str_5A9550 s;
        char *g;
        text_5A9550(&s, sub_00594600(dlg, id == 0x1c8 ? 0x16f : 0x178, 4));
        g = *(char **)(ED + 0x68);
        if (g && *(int *)(g + 0x354) == (id == 0x1c8 ? 7 : 5)) {
            if (id == 0x1c8)
                sub_0054EA10(*(void **)(g + 0x1bc), &s);
            else
                sub_005AC4A0(*(void **)(g + 0x1bc), &s);
        }
        imp_00607330(&s);
        break;
    }
    case 0x1cb:
        anims_5A9550(dlg, ctrl);
        break;
    case 0x1cc: {
        Str_5A9550 a, b, c, d, bv;
        text_5A9550(&a, sub_00594600(dlg, 0x151, 4));
        stem_5A9550(&a);
        text_5A9550(&b, sub_00594600(dlg, 0x154, 4));
        stem_5A9550(&b);
        text_5A9550(&c, sub_00594600(dlg, 0x165, 4));
        stem_5A9550(&c);
        text_5A9550(&d, sub_00594600(dlg, 0x167, 4));
        stem_5A9550(&d);
        imp_00607334(&bv, &b);
        sub_005ACE90(ED, 0, &a, bv, &c, &d);
        imp_00607330(&d);
        imp_00607330(&c);
        imp_00607330(&b);
        imp_00607330(&a);
        break;
    }
    }
    if (event != 0x601)
        return;
    switch (id) {
    case 0x159:
    case 0x184:
    case 0x1dd:
    case 0x179:
    case 0x191:
    case 0x170:
    case 0x1d4:
        sub_005B1C10(ED, value_5A9550(ctrl));
        break;
    case 0x15a:
    case 0x185:
    case 0x1de:
    case 0x17a:
    case 0x192:
    case 0x171:
        sub_005B1C60(ED, value_5A9550(ctrl));
        break;
    case 0x15b:
    case 0x186:
    case 0x1df:
    case 0x17b:
    case 0x193:
    case 0x172:
    case 0x1d5:
        sub_005B1CB0(ED, value_5A9550(ctrl));
        break;
    case 0x15d:
        sub_005B1D00(ED, value_5A9550(ctrl));
        break;
    case 0x15e:
    case 0x188:
    case 0x1e1:
    case 0x17d:
    case 0x195:
        sub_005B1D50(ED, value_5A9550(ctrl));
        break;
    case 0x15f:
        sub_005B1DA0(ED, value_5A9550(ctrl));
        break;
    case 0x161:
        sub_005B1DF0(ED, value_5A9550(ctrl));
        break;
    case 0x162:
        sub_005B1E40(ED, value_5A9550(ctrl));
        break;
    case 0x163:
        sub_005B1E90(ED, value_5A9550(ctrl));
        break;
    case 0x1c7: {
        const char *t = sub_00592C30(*(void **)(ctrl + 0x54));
        char *g = *(char **)(ED + 0x68);
        if (g && *(int *)(g + 0x354) == 7) {
            void *o = *(void **)(g + 0x1bc);
            float a = (float)imp_atof(t);
            double ad = a;
            float b = (float)imp_atof(t);
            sub_0054D350(o, 0, (float)(b * ad));
        }
        break;
    }
    case 0x1d6: {
        const char *t = sub_00592C30(*(void **)(ctrl + 0x54));
        char *g = *(char **)(ED + 0x68);
        if (g)
            sub_005A1350(*(void **)(g + 0x1bc), (float)imp_atof(t));
        break;
    }
    }
}
