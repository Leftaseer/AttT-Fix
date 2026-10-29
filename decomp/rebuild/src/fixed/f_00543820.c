/* 0x00543820: CTacticLevel set-up (the loader whose progress 0x004FDFD0 advances, the hero type): a render list
 * (+0xB8, 0x004F62C0), three callbacks (0x0053E4A0, 0x0053B9E0, 0x0053A9B0) chained into 0x006CAA08/10/18, +0x8C
 * (0x00427990); then each component name of the level (+0x7C +0x0C, 0x1C apart) is built:
 *   sky, clouds (added and their +0x1DC put on the list +0x314), sun (kept), continent (Continent<n>[Edit],
 *   0x00528C10, at +0x98; the camera limits from its box (0x0043DF90), a tactic render list 0x004CEA30, the sun's
 *   +0x58 and the continent's +0x1C4 on the list; a forest anywhere makes +0x78 (0x00555690));
 *   shadows, hero (the glow circle +0x30C, 0x005413C0), objects (+0x7C +0x100, 0x50 apart, 0x0047B060), houses
 *   (Continent<n>Towns, 0x0045B9B0, every Town entry 0x0053B490, the town meshes to the renderer +0xCC), grass
 *   (when +0xF4 is empty: the grass map, the tufts into +0x100 (0x00524C00), the other plants 0x0052E020 into
 *   +0xF0, the butterflies +0x104), forest, trees (0x00555160), water (+0x108, 0x004F8670), flares, icons (the
 *   script's GUIScene.WorldLevel.scene and Load, +0xD0), enemies (0x006CA9BC, the editor's 0x008D1304,
 *   0x0053A700) and npc (nothing);
 * then the forest's colours (0x0042F160), the progress made up to 16 and the options Shadow, Shadow_Units,
 * Reflection and Grass applied */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_543820;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_543820;                 /* nScript::Table */
typedef struct { unsigned int alloc; void **head; unsigned int size; } List_543820;
typedef struct { void *vt; float x, y, z; unsigned char flag, pad[3]; float h; } Label_0045E830;
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void __cdecl sub_005E3E9C(void *p);                        /* operator delete */
DECOMP_C void *__cdecl sub_005E436E(void *p, int vfdelta, void *src, void *dst, int isref);  /* __RTDynamicCast */
DECOMP_C void *__thiscall sub_004F62C0(void *self);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C unsigned int __thiscall sub_00433A60(void *self);
DECOMP_C void __thiscall sub_005540F0(void *self);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __thiscall sub_004FDFD0(void *self, int step);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void *__thiscall sub_0044D030(void *self, void *out, const void *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C unsigned char __thiscall sub_0057AA20(void *self, const char *key);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C char *__cdecl sub_004E1060(void);
DECOMP_C char *__cdecl sub_004E0FB0(void);
DECOMP_C char *__cdecl sub_004E1110(void);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void *__thiscall sub_00528C10(void *self, void *level, void *rd, void *name);
DECOMP_C void __thiscall sub_0043DF90(void *self, void *rect, int a, int b, int c);
DECOMP_C void __cdecl sub_00435AA0(void);
DECOMP_C void __thiscall sub_004B8600(void *self);
DECOMP_C void *__thiscall sub_004CEA30(void *self);
DECOMP_C void __thiscall sub_004714C0(void *self, void *p);
DECOMP_C void *__thiscall sub_00555690(void *self);
DECOMP_C void *__thiscall sub_0053EB20(void *self, const char *name, int a, int b, int c);
DECOMP_C void __thiscall sub_005413C0(void *self, int hero);
DECOMP_C void *__thiscall sub_0047B060(void *self, void *rec, void *pos, int a);
DECOMP_C void __thiscall sub_004AC8D0(void *self, void *m);
DECOMP_C void __thiscall sub_00432620(void *self, const char *name);
DECOMP_C void __cdecl sub_0045B9B0(void *a, void *b, void *c, void *d, void *e, void *f);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_00403080(void *L);                        /* lua_pushnil */
DECOMP_C int __cdecl sub_00403B00(void *L, int idx);                /* lua_next */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C void __cdecl sub_00402BF0(void *L, int idx);               /* lua_pushvalue */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                  /* luaL_ref */
DECOMP_C Tbl_543820 *__stdcall sub_0045C850(Tbl_543820 *out);
DECOMP_C void __thiscall sub_0045C920(void *self);
DECOMP_C Str_543820 *__cdecl sub_0047CE00(unsigned int ebx, Str_543820 *out);
DECOMP_C void __thiscall sub_0053B490(void *self, void *key, void *val);
DECOMP_C void __thiscall sub_005AD210(void *self, void *obj);
DECOMP_C void __thiscall sub_0057C220(void *self, const char *key);
DECOMP_C void __thiscall sub_004B7F20(void *self);
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C List_543820 *__thiscall sub_004CD030(void *self, void *out);
DECOMP_C void __thiscall sub_004B68E0(void *self, void *where, void *first, void *last, void *tag);
DECOMP_C void __thiscall sub_004B6CC0(void *self, void *o);
DECOMP_C void *__cdecl sub_00433BD0(void);
DECOMP_C void __thiscall sub_005302E0(void *self, void *map, void *mask);
DECOMP_C void *__thiscall sub_00524C00(void *self);
DECOMP_C void __thiscall sub_0053A560(void *self, int i, Str_543820 s);
DECOMP_C void __thiscall sub_0053A5C0(void *self, int i, Str_543820 s);
DECOMP_C void __thiscall sub_0053A620(void *self, int i, Str_543820 s);
DECOMP_C void __thiscall sub_00524890(void *self);
DECOMP_C void *__thiscall sub_0052E020(void *self, void *rec, void *pos, unsigned int a, unsigned int b, float c);
DECOMP_C void __thiscall sub_0052FE60(void *self);
DECOMP_C void __thiscall sub_005A3680(void *self, void *val);
DECOMP_C void *__thiscall sub_00434B50(void *self, void *name);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C void __thiscall sub_00555160(void *self, void *name, Label_0045E830 l);
DECOMP_C void *__thiscall sub_004F8670(void *self, void *rec, unsigned int a, void *level, void *list);
DECOMP_C void *__thiscall sub_0052B9C0(void *self, void *sun);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const void *key);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void __thiscall sub_0057C2D0(void *self, const char *key, void *obj);
DECOMP_C void *__thiscall sub_0057B770(void *t, void *out, const char *key);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void *__thiscall sub_00527960(void *self);
DECOMP_C void __cdecl sub_0053A700(void);
DECOMP_C void __cdecl sub_0053E4A0(void);
DECOMP_C void __cdecl sub_0053B9E0(void);
DECOMP_C void __cdecl sub_0053A9B0(void);
DECOMP_C char d_0061AE24[], d_006CAA08[], d_006CAA10[], d_006CAA18[], d_0061597C[], d_00615A1C[], d_00614EB0[],
    d_0061B12C[], d_0060AB6C[], d_0060ACA4[], d_00612788[], d_0061B124[], d_0061B11C[], d_0061B114[], d_00612AE0[],
    d_0061323C[], d_00608A70[], d_0061B0F4[], d_0061B0EC[], d_0061B0E4[], d_0061B0DC[], d_006C88D4[], d_0061B0D4[],
    d_008D122C[], d_0060B97C[], d_00607CC4[], d_006BF0C8[], d_006C0900[], d_0061B0CC[], d_0061B0B4[], d_0061B090[],
    d_0061B084[], d_0061B078[], d_0060979C[], d_0061B070[], d_0060B914[], d_00611BBC[], d_00615328[], d_0060C598[],
    d_006CAA34[], d_0060AD08[], d_0061414C[], d_0060FF88[], d_0061B068[], d_006CA9BC[], d_008D1304[], d_0061B064[],
    d_0060ADC0[], d_0060AD00[], d_0060ADB0[], d_0060ADA0[], d_0060AD94[], d_0060ADB8[], d_0068AE10[], d_006C88D8[];
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C char *(__cdecl *imp_itoa)(int, char *, int) __asm__("__imp___itoa");
DECOMP_C int (__cdecl *imp_sprintf)(char *, const char *, ...) __asm__("__imp__sprintf");
typedef void (__thiscall *vfp_543820)(void *self, void *p);
typedef void (__thiscall *vf0_543820)(void *self);
typedef void (__thiscall *vfpi_543820)(void *self, void *p, int a);

#define LS (*(void **)d_008D122C)
#define REG (-10000)
#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define EQ(s, lit) imp_006071E4(s, lit)
#define ADD(this, o) ((vfp_543820)VF((this) + 4, 4))((this) + 4, (void *)(o))
#define EDITOR (*(char *)(*(char **)d_006C88D8 + 0x40))
#define LVL(this) (*(char **)((this) + 0x7c))

/* a callback node (0x18) chained in front of *head */
static void hook_543820(char *this, char *head, void (*fn)(void))
{
    unsigned int *n = (unsigned int *)sub_005E3EAE(0x18);
    if (n) {
        n[1] = *(unsigned int *)head;
        n[0] = (unsigned int)(size_t)d_0061AE24;
        n[2] = (unsigned int)(size_t)this;
        n[4] = (unsigned int)(size_t)fn;
        n[5] = 0;
    }
    *(unsigned int **)head = n;
}

static void *list_543820(void)
{
    void *o = sub_005E3EAE(0x50);
    return o ? sub_004F62C0(o) : 0;
}

/* p put at the end of the list +0x314 */
static void push_543820(char *this, void *p)
{
    char **head = *(char ***)(this + 0x318);
    char **n = sub_005AD6C0(head, (char **)head[1], &p);
    sub_004E0EF0(this + 0x314, 1);
    head[1] = (char *)n;
    *(char ***)n[1] = n;
}

/* WorldLevel.curContinent */
static int continent_543820(void)
{
    Tbl_543820 t;
    int n = (int)(long long)sub_0057AD40(sub_004323E0(&t, d_0060AB6C), d_0060ACA4);
    sub_004220A0(&t);
    return n;
}

static void free_543820(void **head)
{
    void **n = (void **)*head;
    head[0] = head;
    head[1] = head;
    while (n != head) {
        void **next = (void **)*n;
        sub_005E3E9C(n);
        n = next;
    }
}

static void continent_543820f(char *this)
{
    char buf[0x20];
    Str_543820 s1, s2, s3;
    void *o;
    imp_itoa(continent_543820(), buf, 10);
    o = sub_005E3EAE(0x2e0);
    if (EDITOR) {
        if (o) {
            imp_00607324(&s1, d_00612788);
            imp_006071DC(&s2, &s1, buf);
            imp_006071DC(&s3, &s2, d_0061B124);
            o = sub_00528C10(o, this, *(void **)(this + 0xcc), &s3);
            *(void **)(this + 0x98) = o;
            imp_00607330(&s3);
            imp_00607330(&s2);
            imp_00607330(&s1);
        } else
            *(void **)(this + 0x98) = 0;
    } else {
        if (o) {
            imp_00607324(&s1, d_00612788);
            imp_006071DC(&s2, &s1, buf);
            o = sub_00528C10(o, this, *(void **)(this + 0xcc), &s2);
            *(void **)(this + 0x98) = o;
            imp_00607330(&s2);
            imp_00607330(&s1);
        } else
            *(void **)(this + 0x98) = 0;
    }
    ADD(this, *(void **)(this + 0x98));
}

static void hero_543820(char *this, void *loader, int hero, unsigned int *count)
{
    Str_543820 s;
    char *o = (char *)sub_005E3EAE(0x1ac);
    o = o ? (char *)sub_0053EB20(o, d_0061323C, 2, 2, 0) : 0;
    *(char **)(this + 0x30c) = o;
    *(unsigned int *)(o + 0x70) = *(unsigned int *)d_00608A70;
    *(unsigned int *)(o + 0x78) = *(unsigned int *)d_00608A70;
    o[0x7c] = 1;
    imp_00607324(&s, d_0061B0F4);
    o = *(char **)(this + 0x30c);
    ((vfpi_543820)VF(o, 0x38))(o, &s, 0);
    imp_00607330(&s);
    o = *(char **)(this + 0x30c);
    ((vf0_543820)VF(o, 0x50))(o);
    ADD(this, *(void **)(this + 0x30c));
    sub_005413C0(this, hero);
    ++*count;
    sub_004FDFD0(loader, 1);
}

static void objects_543820(char *this)
{
    unsigned int i;
    int off;
    for (i = 0, off = 0;; i++, off += 0x50) {
        char *b = *(char **)(LVL(this) + 0x100), *o;
        if (!b || i >= (unsigned int)((int)(*(char **)(LVL(this) + 0x104) - b) / 0x50))
            break;
        o = (char *)sub_005E3EAE(0x24c);
        if (o) {
            char *r = *(char **)(LVL(this) + 0x100) + off;
            o = (char *)sub_0047B060(o, r, r + 0x34, 1);
        }
        sub_004AC8D0(o, *(char **)(LVL(this) + 0x100) + off + 0x1c);
        *(float *)(o + 0x78) = *(float *)(*(char **)(LVL(this) + 0x100) + off + 0x30);
        o[0x80] = 1;
        ADD(this, o);
        push_543820(this, o + 0x1dc);
    }
}

/* every entry of the table t counted, or (with this) given to 0x0053B490 */
static int towns_543820(char *this, Tbl_543820 *t, void *loader, unsigned int *count, int k)
{
    unsigned int it[3];
    int i = 0;
    sub_00403390(LS, REG, (int)t->w[2]);
    it[1] = 0;
    it[0] = (unsigned int)(size_t)d_0060B97C;
    sub_00403080(LS);
    *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
    while (!*(unsigned char *)&it[2]) {
        if (this) {
            Tbl_543820 v, *pv;
            Str_543820 key;
            pv = sub_0045C850(&v);
            sub_0053B490(this, sub_0047CE00(0, &key), pv);
            imp_00607330(&key);
            sub_004220A0(&v);
            if (i == k || i == k * 2 || i == k * 3 || i == k * 4 || i == k * 5 || i == k * 6 || i == k * 7 ||
                i == k * 8) {
                *count += 2;
                sub_004FDFD0(loader, 2);
            }
            sub_00402A70(LS, -2);
            *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
            i++;
        } else {
            i++;
            sub_00402A70(LS, -2);
            *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
        }
    }
    sub_0045C920(it);
    return i;
}

static void houses_543820(char *this, void *loader, unsigned int *count, void **houses, char *rl)
{
    char buf[0x20];
    Str_543820 s1, s2, s3;
    Tbl_543820 town;
    List_543820 l, tmp, *t;
    void **n, **head;
    char *r;
    int k;
    if (!*houses)
        *houses = list_543820();
    *(void **)(this + 0x114) = list_543820();
    imp_itoa(continent_543820(), buf, 10);
    imp_00607324(&s1, d_00612788);
    imp_006071DC(&s2, &s1, buf);
    imp_006071DC(&s3, &s2, d_0061B0DC);
    imp_00607330(&s2);
    imp_00607330(&s1);
    sub_00432620(*(void **)d_006C88D4, imp_0060732C(&s3));
    sub_0045B9B0(*(void **)(this + 0xe0), *(void **)(this + 0x78), *houses, this + 0x314, this, rl);
    ++*count;
    sub_004FDFD0(loader, 1);
    sub_004323E0(&town, d_0061B0D4);
    k = towns_543820(0, &town, loader, count, 0) / 8;
    towns_543820(this, &town, loader, count, k);
    ADD(this, rl);
    ++*count;
    sub_004FDFD0(loader, 1);
    if (EDITOR) {
        char *h = *(char **)(this + 0x114);
        ADD(this, h ? h + 0x18 : 0);
        sub_005AD210(*(void **)d_006C88D8, 0);
    } else {
        Tbl_543820 g;
        g.w[1] = 0;
        g.w[0] = (unsigned int)(size_t)d_00607CC4;
        sub_00402BF0(LS, -10002);
        g.w[2] = (unsigned int)sub_00402190(LS, REG);
        sub_0057C220(&g, d_0061B0D4);
        sub_004220A0(&g);
    }
    r = rl + 0x38;
    sub_004B7F20(r);
    l.head = sub_004C2F40();
    l.size = 0;
    t = sub_004CD030(r, &tmp);
    if (&l != t) {
        void **last = t->head, **first = (void **)*last;
        free_543820(l.head);
        l.size = 0;
        sub_004B68E0(&l, *l.head, first, last, first);
    }
    free_543820(tmp.head);
    tmp.size = 0;
    sub_005E3E9C(tmp.head);
    tmp.head = 0;
    head = l.head;
    for (n = (void **)*head; n != head; n = (void **)*n) {
        char *o = (char *)sub_005E436E(n[2], 0, d_006BF0C8, d_006C0900, 0);
        sub_004B6CC0(*(void **)(this + 0xcc), o ? o + 0x24c : 0);
    }
    ++*count;
    sub_004FDFD0(loader, 1);
    free_543820(head);
    l.size = 0;
    sub_005E3E9C(head);
    sub_004220A0(&town);
    imp_00607330(&s3);
}

static void grass_543820(char *this)
{
    char map[0x400], mask[0x400];
    Str_543820 smask, smap;
    unsigned int i, j = 0;
    int off = 0, n = continent_543820();
    char *o;
    imp_sprintf(map, d_0061B0B4, n);
    imp_sprintf(mask, d_0061B090, n);
    imp_00607324(&smask, mask);
    imp_00607324(&smap, map);
    sub_005302E0(sub_00433BD0(), &smap, &smask);
    imp_00607330(&smap);
    imp_00607330(&smask);
    o = (char *)sub_005E3EAE(0x278);
    *(void **)(this + 0x100) = o ? sub_00524C00(o) : 0;
    for (i = 0;; i++, off += 0x78) {
        char *b = *(char **)(LVL(this) + 0x88), *r;
        if (!b || i >= (unsigned int)((int)(*(char **)(LVL(this) + 0x8c) - b) / 0x78))
            break;
        if (EQ(b + off, d_0061B084) || EQ(*(char **)(LVL(this) + 0x88) + off, d_0061B078)) {
            Str_543820 s;
            char *g;
            imp_00607334(&s, *(char **)(LVL(this) + 0x88) + off);
            sub_0053A560(*(void **)(this + 0x100), j, s);
            imp_00607334(&s, *(char **)(LVL(this) + 0x88) + off + 0x1c);
            sub_0053A5C0(*(void **)(this + 0x100), j, s);
            imp_00607334(&s, *(char **)(LVL(this) + 0x88) + off + 0x38);
            sub_0053A620(*(void **)(this + 0x100), j, s);
            g = *(char **)(this + 0x100);
            *(int *)(g + 0x24c + j * 4) = (int)*(float *)(*(char **)(LVL(this) + 0x88) + off + 0x74);
            if (++j == 2) {
                sub_00524890(*(void **)(this + 0x100));
                (*(char **)(this + 0x100))[0x1c9] = (*(char **)(this + 0x8c))[0x6a];
                ADD(this, *(void **)(this + 0x100));
            }
        } else {
            void *p;
            o = (char *)sub_005E3EAE(0x2b0);
            if (o) {
                r = *(char **)(LVL(this) + 0x88) + off;
                o = (char *)sub_0052E020(o, r, r + 0x58, *(unsigned short *)(r + 0x54),
                                         *(unsigned short *)(r + 0x56), *(float *)(r + 0x74));
            }
            p = o;
            if ((*(char **)(this + 0x8c))[0x6a])
                sub_0052FE60(o);
            o[0x1c5] = (*(char **)(this + 0x8c))[0x6a];
            r = *(char **)(LVL(this) + 0x88) + off;
            ((vfpi_543820)VF(o, 0x38))(o, r + 0x1c, 0);
            r = *(char **)(LVL(this) + 0x88) + off;
            ((vfpi_543820)VF(o, 0x2c))(o, r + 0x38, 1);
            ADD(this, o);
            sub_005A3680(this + 0xf0, &p);
        }
    }
    o = (char *)sub_005E3EAE(0xc4);
    if (o) {
        Str_543820 s;
        imp_00607324(&s, d_0060979C);
        *(void **)(this + 0x104) = sub_00434B50(o, &s);
        imp_00607330(&s);
    } else
        *(void **)(this + 0x104) = 0;
    sub_004205C0(this, *(void **)(this + 0x104));
}

static void trees_543820(char *this)
{
    unsigned int i;
    int off;
    for (i = 0, off = 0;; i++, off += 0x34) {
        char *b = *(char **)(LVL(this) + 0xb8), *r;
        Label_0045E830 l;
        if (!b || i >= (unsigned int)((int)(*(char **)(LVL(this) + 0xbc) - b) / 0x34))
            break;
        r = b + off;
        l.h = *(float *)(r + 0x30);
        l.vt = d_0060B914;
        l.x = *(float *)(r + 0x20);
        l.y = *(float *)(r + 0x24);
        l.z = *(float *)(r + 0x28);
        l.flag = *(unsigned char *)(r + 0x2c);
        sub_00555160(*(void **)(this + 0x78), *(char **)(LVL(this) + 0xb8) + off, l);
    }
}

static void water_543820(char *this, void *loader, unsigned int *count)
{
    int n = continent_543820() - 1;
    char *o = (char *)sub_005E3EAE(0x270), *w;
    if (o) {
        char *r = *(char **)(LVL(this) + 0x70) + n * 0x30;
        o = (char *)sub_004F8670(o, r, *(unsigned int *)(r + 0x2c), this, this + 0x314);
    }
    *(char **)(this + 0x108) = o;
    ADD(this, o);
    w = *(char **)(LVL(this) + 0x70);
    o = *(char **)(this + 0x108);
    {
        unsigned int z = *(unsigned int *)(w + 0x24), y = *(unsigned int *)(w + 0x20),
                     x = *(unsigned int *)(w + 0x1c);
        *(unsigned int *)(o + 0x58) = *(unsigned int *)(o + 0x64);
        *(unsigned int *)(o + 0x5c) = *(unsigned int *)(o + 0x68);
        *(unsigned int *)(o + 0x60) = *(unsigned int *)(o + 0x6c);
        *(unsigned int *)(o + 0x64) = x;
        *(unsigned int *)(o + 0x68) = y;
        *(unsigned int *)(o + 0x6c) = z;
    }
    o[0x70] = 1;
    *(unsigned int *)(o + 0x78) = *(unsigned int *)(*(char **)(LVL(this) + 0x70) + 0x28);
    o[0x80] = 1;
    sub_004FDFD0(loader, 2);
    *count += 2;
}

static void icons_543820(char *this, void *houses)
{
    Tbl_543820 t, g, w;
    unsigned int fn[8], res[8];
    char *o;
    if (houses)
        ADD(this, (char *)houses + 0x18);
    o = *(char **)(this + 0xb8);
    ADD(this, o ? o + 0x18 : 0);
    if (*(char **)d_006CAA34)
        ADD(this, *(void **)(*(char **)d_006CAA34 + 0x44));
    t.w[1] = 0;
    t.w[0] = (unsigned int)(size_t)d_00607CC4;
    t.w[2] = 0xffffffffu;
    sub_0057A860(&t, sub_0057B4E0(sub_004323E0(&g, d_0060AD08), &w, d_0060AB6C));
    sub_004220A0(&w);
    sub_004220A0(&g);
    sub_0057C2D0(&t, d_0061414C, this + 0x74);
    sub_0057A180(sub_0057B770(&t, fn, d_0060FF88), res, 0);
    sub_00427820(res);
    sub_004378D0(fn);
    o = (char *)sub_005E3EAE(0x60);
    o = o ? (char *)sub_00527960(o) : 0;
    *(char **)(this + 0xd0) = o;
    ADD(this, o);
    ADD(this, *(void **)(*(char **)(this + 0xe8) + 0x128));
    sub_004220A0(&t);
}

DECOMP(00543820)
void __thiscall f_00543820(void *self, void *loader, int hero)
{
    char *this = (char *)self;
    char *names = LVL(this) + 0xc, *sun = 0, *rl;
    void *houses = 0;
    unsigned int count = 0, i;
    Tbl_543820 g, c, opt;
    struct { Tbl_543820 t; const char *k; } p;
    struct { void *t; const char *k; } ref;
    char *o;
    *(void **)(this + 0xb8) = list_543820();
    hook_543820(this, d_006CAA08, sub_0053E4A0);
    hook_543820(this, d_006CAA10, sub_0053B9E0);
    hook_543820(this, d_006CAA18, sub_0053A9B0);
    *(char **)(this + 0x8c) = sub_00427990();
    rl = 0;
    i = 0;
    if (sub_00433A60(names) > 0) {
        do {
            char *name = *(char **)(names + 4) + i * 0x1c;
            int add = 0;
            o = 0;
            if (EQ(name, d_0061597C)) {
                o = sub_004E1060();
                add = 1;
            } else if (EQ(*(char **)(names + 4) + i * 0x1c, d_00615A1C)) {
                sun = sub_004E0FB0();
                ((vfp_543820)VF(this + 4, 0xc))(this + 4, sun);
            } else if (EQ(*(char **)(names + 4) + i * 0x1c, d_00614EB0)) {
                o = sub_004E1110();
                add = 1;
            } else if (EQ(*(char **)(names + 4) + i * 0x1c, d_0061B12C)) {
                float rect[4], w, h, *b;
                char *e;
                continent_543820f(this);
                b = (float *)(*(char **)(*(char **)(*(char **)(this + 0x98) + 0x218) + 8) + 0x70);
                w = b[1] - b[0];
                rect[0] = b[2];
                h = b[2] - b[3];
                rect[1] = b[0];
                rect[2] = w;
                rect[3] = h;
                sub_0043DF90(*(void **)(this + 0xec), rect, (int)(long long)(w / h * *(double *)d_0068AE10), 1000,
                             0x14);
                sub_00435AA0();
                sub_004B8600(*(void **)(this + 0xcc));
                o = (char *)sub_005E3EAE(0xdc);
                rl = o ? (char *)sub_004CEA30(o) : 0;
                if (sun) {
                    void *q = sun + 0x58;
                    sub_004714C0(this + 0x314, &q);
                }
                count++;
                sub_004FDFD0(loader, 1);
                o = *(char **)(this + 0x98);
                push_543820(this, o ? o + 0x1c4 : 0);
                for (e = *(char **)(names + 4); e != *(char **)(names + 8); e += 0x1c)
                    if (EQ(e, d_0061B11C)) {
                        o = (char *)sub_005E3EAE(0x130);
                        *(void **)(this + 0x78) = o ? sub_00555690(o) : 0;
                        break;
                    }
            }
            if (add) {
                ((vfp_543820)VF(this + 4, 0xc))(this + 4, o);
                push_543820(this, o ? o + 0x1dc : 0);
            }

#define IS(lit) EQ(*(char **)(names + 4) + i * 0x1c, lit)
            if (IS(d_0061B114))
                ((vfp_543820)VF(this + 4, 0xc))(this + 4, *(void **)(this + 0xcc));
            else if (IS(d_00612AE0))
                hero_543820(this, loader, hero, &count);
            else if (IS(d_0061B0EC)) {
                objects_543820(this);
                sub_004FDFD0(loader, 1);
                count++;
            } else if (IS(d_0061B0E4))
                houses_543820(this, loader, &count, &houses, rl);
            else if (IS(d_0061B0CC) && (!*(char **)(this + 0xf4) ||
                                        (*(char **)(this + 0xf8) - *(char **)(this + 0xf4)) >> 2 == 0)) {
                grass_543820(this);
                sub_004FDFD0(loader, 1);
                count++;
            } else if (IS(d_0061B11C))
                ADD(this, *(void **)(this + 0x78));
            else if (IS(d_0061B070))
                trees_543820(this);
            else if (IS(d_00611BBC))
                water_543820(this, loader, &count);
            else if (IS(d_00615328)) {
                if (sun) {
                    o = (char *)sub_005E3EAE(0x90);
                    ADD(this, o ? sub_0052B9C0(o, sun) : 0);
                }
                o = *(char **)(this + 0x388);
                ADD(this, o ? o + 0x18 : 0);
            } else if (IS(d_0060C598))
                icons_543820(this, houses);
            else if (IS(d_0061B068)) {
                if (!houses)
                    houses = list_543820();
                *(void **)d_006CA9BC = houses;
                if (EDITOR) {
                    o = (char *)list_543820();
                    *(char **)d_008D1304 = o;
                    ADD(this, o ? o + 0x18 : 0);
                }
                sub_0053A700();
                count += 3;
                sub_004FDFD0(loader, 3);
            } else
                IS(d_0061B064);
#undef IS
        } while (++i < sub_00433A60(names));
    }

    if (*(char **)(this + 0x78)) {
        char *col;
        sub_005540F0(*(void **)(this + 0x78));
        col = sub_0042F160();
        *(float *)(**(char ***)(*(char **)(this + 0x78) + 0x68) + 0x58) = *(float *)(col + 0x2c);
        *(float *)(**(char ***)(*(char **)(this + 0x78) + 0x68) + 0x5c) = *(float *)(col + 0x30);
        *(float *)(**(char ***)(*(char **)(this + 0x78) + 0x68) + 0x60) = *(float *)(col + 0x34);
        *(float *)(**(char ***)(*(char **)(this + 0x78) + 0x68) + 0x64) = *(float *)(col + 0x38);
    }
    if (count < 8)
        sub_004FDFD0(loader, 0x10 - count);
    ref.t = sub_004323E0(&g, d_0060AD08);
    ref.k = d_0060AD00;
    sub_0044C0E0(sub_0044D030(&ref, &p, d_0060ADC0), &c);
    sub_00435D90(&opt, &c);
    sub_004220A0(&c);
    sub_004220A0(&p);
    sub_004220A0(&g);
    (*(char **)(this + 0xcc))[0x58] = sub_0057AA20(&opt, d_0060ADB0) ? 1 : 0;
    (*(char **)(this + 0xcc))[0x59] = sub_0057AA20(&opt, d_0060ADA0) ? 1 : 0;
    o = *(char **)(this + 0x108);
    if (sub_0057AA20(&opt, d_0060AD94)) {
        if (o)
            o[0x1dc] = 1;
    } else if (o)
        o[0x1dc] = 0;
    if (sub_0057AA20(&opt, d_0060ADB8))
        (*(char **)(this + 0x100))[0x1c9] = 1;
    else {
        char *v = *(char **)(this + 0xf4);
        int n = v ? (int)(*(char **)(this + 0xf8) - v) >> 2 : 0, k;
        for (k = 0; k < n; k++)
            (*(char **)(*(char **)(this + 0xf4) + k * 4))[0x1c5] = 0;
        (*(char **)(this + 0x100))[0x1c9] = 0;
        if (*(char **)(this + 0x104))
            (*(char **)(this + 0x104))[0x38] = 0;
    }
    sub_004220A0(&opt);
}
