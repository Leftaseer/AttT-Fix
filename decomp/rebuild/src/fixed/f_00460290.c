/* 0x00460290: map location constructor (name, its table, a text kept at +0x27C, the base's last argument): the base
 * (0x005B3FD0), its lists (+0x1F4..+0x23C, +0x258..+0x270), the table at +0x1E8; Pos gives the position (+0x64,
 * the previous one at +0x58, its table at +0x1C4) and Rot the turn (+0x78), then vf A0. Every entry of Objs
 * (0x00460030), Npcs (0x0045E4D0), Saos (0x0045E630), Trees (0x0045E830), Skms (0x0045EA70) and Psps (0x0045EBC0)
 * is added; the lists +0x228, +0x204 and +0x210 are handed back to 0x006C8E50 and emptied, the list +0x240 to the
 * game's (0x0042F160) +0x70 (0x0053A6B0). Its DrawableBBox (+0x1A8, 0x00592020) gets a box the original never fills
 * (stack left-overs; left uninitialised here too). In the editor (0x006C88D8 +0x40) Editor.houseColor colours its
 * axis line (+0x298, 0x00425B50); otherwise the line and the tables +0x1C4..+0x1E8 are released. Returns this */
/* @conv ECX 16 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_460290;                 /* nScript::Table */
DECOMP_C void __thiscall sub_005B3FD0(void *self, void *name, int a, unsigned int b);
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void *__thiscall sub_0057B5A0(void *self, Tbl_460290 *out, const char *key, Tbl_460290 *def);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_00403080(void *L);                        /* lua_pushnil */
DECOMP_C int __cdecl sub_00403B00(void *L, int idx);                /* lua_next */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C void __cdecl sub_00402270(void *L, int t, int ref);        /* luaL_unref */
DECOMP_C Tbl_460290 *__stdcall sub_0045C850(Tbl_460290 *out);
DECOMP_C void __thiscall sub_0045C920(void *self);
DECOMP_C void __thiscall sub_00460030(void *self, void *v);
DECOMP_C void __thiscall sub_0045E4D0(void *self, void *v);
DECOMP_C void __thiscall sub_0045E630(void *self, void *v);
DECOMP_C void __cdecl sub_0045E830(void *self, unsigned int ebx, void *v);
DECOMP_C void __thiscall sub_0045EA70(void *self, void *v);
DECOMP_C void __thiscall sub_0045EBC0(void *self, void *v);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __thiscall sub_0053A6B0(void *self, void *o);
DECOMP_C void __cdecl sub_005E3E9C(void *p);                        /* operator delete */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_00592020(void *self, void *owner, const void *box, int kind);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00425B50(void *self, float x0, float y0, float z0, float x1, float y1, float z1,
                                       unsigned int color);
DECOMP_C char d_0060BB98[], d_0060B9C0[], d_0060BB90[], d_0060BB88[], d_0060BB80[], d_0060BB78[], d_0060BB70[],
    d_0060BB68[], d_0060BB60[], d_0060BB54[], d_0060BB50[], d_0060B97C[], d_008D122C[], d_006C8E50[], d_006C88D8[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
typedef void (__thiscall *vf0_460290)(void *self);
typedef void (__thiscall *vfp_460290)(void *self, void *p);
typedef void (__thiscall *vfi_460290)(void *self, int a);

#define LS (*(void **)d_008D122C)
#define REG (-10000)
#define VF(o, off) ((*(void ***)(o))[(off) / 4])

typedef void (*each_460290)(char *this, void *v);

static void objs_460290(char *this, void *v) { sub_00460030(this, v); }
static void npcs_460290(char *this, void *v) { sub_0045E4D0(this, v); }
static void saos_460290(char *this, void *v) { sub_0045E630(this, v); }
static void trees_460290(char *this, void *v) { sub_0045E830(this, 0, v); }
static void skms_460290(char *this, void *v) { sub_0045EA70(this, v); }
static void psps_460290(char *this, void *v) { sub_0045EBC0(this, v); }

/* every value of the table t */
static void each_460290f(char *this, Tbl_460290 *t, each_460290 fn)
{
    unsigned int it[3];
    if ((int)t->w[2] <= 0)
        return;
    sub_00403390(LS, REG, (int)t->w[2]);
    it[1] = 0;
    it[0] = (unsigned int)(size_t)d_0060B97C;
    sub_00403080(LS);
    *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
    while (!*(unsigned char *)&it[2]) {
        Tbl_460290 v;
        fn(this, sub_0045C850(&v));
        sub_004220A0(&v);
        sub_00402A70(LS, -2);
        *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
    }
    sub_0045C920(it);
}

/* t = this+0x1E8 [key] */
static void field_460290(char *this, Tbl_460290 *t, const char *key)
{
    Tbl_460290 nil = { { 0x607cc4, 0, 0xffffffffu } }, tmp;
    sub_0057A860(t, sub_0057B5A0(this + 0x1e8, &tmp, key, &nil));
    sub_004220A0(&tmp);
    sub_004220A0(&nil);
}

static void empty_460290(char *this, int off)
{
    void **n = (void **)**(void ***)(this + off);
    **(void ***)(this + off) = *(void **)(this + off);
    (*(void ***)(this + off))[1] = *(void **)(this + off);
    *(int *)(this + off + 4) = 0;
    while (n != *(void ***)(this + off)) {
        void **next = (void **)*n;
        sub_005E3E9C(n);
        n = next;
    }
}

/* the list at +off handed back to 0x006C8E50 and emptied */
static void back_460290(char *this, int off)
{
    void **head = *(void ***)(this + off), **n;
    for (n = (void **)*head; n != head; n = (void **)*n) {
        char *o = *(char **)d_006C8E50 + 4;
        ((vfp_460290)VF(o, 4))(o, n[2]);
    }
    empty_460290(this, off);
}

/* the refcounted pointer at +off takes p */
static void set_460290(char *this, int off, unsigned int *p)
{
    unsigned int *old;
    if (p)
        p[1]++;
    old = *(unsigned int **)(this + off);
    if (old && --old[1] == 0)
        ((vfi_460290)VF(old, 0))(old, 1);
    *(unsigned int **)(this + off) = p;
}

static void unref_460290(char *this, int off)
{
    if (*(int *)(this + off) > 0) {
        sub_00402270(LS, REG, *(int *)(this + off));
        *(int *)(this + off) = -1;
    }
}

DECOMP(00460290)
void *__thiscall f_00460290(void *self, void *name, void *tbl, void *text, unsigned int b)
{
    char *this = (char *)self;
    static const short lists[] = { 0x1f4, 0x200, 0x20c, 0x218, 0x224, 0x230, 0x23c };
    Tbl_460290 pos, objs;
    unsigned char box[0x60];
    unsigned int i;
    void *mem;
    unsigned int *p;

    sub_005B3FD0(this, name, 0, b);
    *(unsigned int *)this = 0x60bba4;
    for (i = 0; i < 7; i++) {
        *(void ***)(this + lists[i] + 4) = sub_004C2F40();
        *(int *)(this + lists[i] + 8) = 0;
    }
    *(int *)(this + 0x24c) = 0;
    *(int *)(this + 0x250) = 0;
    *(int *)(this + 0x254) = 0;
    for (i = 0; i < 3; i++) {
        *(void ***)(this + 0x258 + i * 0xc + 4) = sub_004C2F40();
        *(int *)(this + 0x258 + i * 0xc + 8) = 0;
    }
    imp_00607334(this + 0x27c, text);
    *(int *)(this + 0x298) = 0;
    *(int *)(this + 0x2a0) = 0;
    *(int *)(this + 0x2a4) = 0;
    *(int *)(this + 0x2a8) = 0;
    sub_0057A860(this + 0x1e8, tbl);
    {
        struct { void *t; const char *k; } ref;
        Tbl_460290 t;
        float x, y, z;
        unsigned int o0, o1, o2;
        ref.t = tbl;
        ref.k = d_0060BB98;
        sub_004369F0(&ref, &t);
        sub_00435D90(&pos, &t);
        sub_004220A0(&t);
        z = sub_0057AC90(&pos, 3);
        y = sub_0057AC90(&pos, 2);
        x = sub_0057AC90(&pos, 1);
        o0 = *(unsigned int *)(this + 0x64);
        o2 = *(unsigned int *)(this + 0x6c);
        o1 = *(unsigned int *)(this + 0x68);
        *(float *)(this + 0x64) = x;
        *(unsigned int *)(this + 0x58) = o0;
        *(float *)(this + 0x68) = y;
        *(unsigned int *)(this + 0x5c) = o1;
        *(unsigned int *)(this + 0x60) = o2;
        *(float *)(this + 0x6c) = z;
        this[0x70] = 1;
    }
    sub_0057A860(this + 0x1c4, &pos);
    *(float *)(this + 0x78) = sub_0057AD40(tbl, d_0060B9C0);
    this[0x80] = 1;
    ((vf0_460290)VF(this, 0xa0))(this);
    {
        Tbl_460290 nil = { { 0x607cc4, 0, 0xffffffffu } };
        sub_0057B5A0(tbl, &objs, d_0060BB90, &nil);
        sub_004220A0(&nil);
    }
    each_460290f(this, &objs, objs_460290);
    field_460290(this, &objs, d_0060BB88);
    each_460290f(this, &objs, npcs_460290);
    field_460290(this, &objs, d_0060BB80);
    each_460290f(this, &objs, saos_460290);
    field_460290(this, &objs, d_0060BB78);
    each_460290f(this, &objs, trees_460290);
    field_460290(this, &objs, d_0060BB70);
    each_460290f(this, &objs, skms_460290);
    field_460290(this, &objs, d_0060BB68);
    each_460290f(this, &objs, psps_460290);
    back_460290(this, 0x228);
    back_460290(this, 0x204);
    back_460290(this, 0x210);
    {
        void *g = *(void **)(sub_0042F160() + 0x70);
        void **head = *(void ***)(this + 0x240), **n;
        for (n = (void **)*head; n != head; n = (void **)*n)
            sub_0053A6B0(g, n[2]);
        empty_460290(this, 0x240);
    }
    mem = sub_005E3EAE(0x380);
    p = mem ? (unsigned int *)sub_00592020(mem, this, box, 1) : 0;
    set_460290(this, 0x1a8, p);
    if (!(*(char **)d_006C88D8)[0x40]) {
        set_460290(this, 0x298, 0);
        unref_460290(this, 0x1cc);
        unref_460290(this, 0x1d8);
        unref_460290(this, 0x1e4);
        unref_460290(this, 0x1f0);
    } else {
        Tbl_460290 ed, t, col;
        struct { void *t; const char *k; } ref;
        unsigned int r, g, bl;
        ref.t = sub_004323E0(&ed, d_0060BB60);
        ref.k = d_0060BB54;
        sub_004369F0(&ref, &t);
        sub_00435D90(&col, &t);
        sub_004220A0(&t);
        sub_004220A0(&ed);
        r = (unsigned int)(long long)sub_0057AC90(&col, 1);
        g = (unsigned int)(long long)sub_0057AC90(&col, 2);
        bl = (unsigned int)(long long)sub_0057AC90(&col, 3);
        mem = sub_005E3EAE(0x1d0);
        p = mem ? (unsigned int *)sub_00425B50(mem, 0.0f, 0.0f, 0.0f, 0.0f, *(float *)d_0060BB50, 0.0f,
                                               (r & 0xff) << 16 | (g & 0xff) << 8 | (bl & 0xff)) : 0;
        set_460290(this, 0x298, p);
        sub_004220A0(&col);
    }
    sub_004220A0(&objs);
    sub_004220A0(&pos);
    return this;
}
