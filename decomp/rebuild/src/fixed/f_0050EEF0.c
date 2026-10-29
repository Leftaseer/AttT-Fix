/* 0x0050EEF0: the tactic battle's input step (unless +0x284 has reached 0x0060FAC0): the board's highlight (+0x48
 * +0x44) and the target marker (+0x210) are dropped; the pressed keys (+0x6C +0x660: side, pressed) run the side's
 * turn end (0x0050B9A0), the AI's (0x005083E0, else 0x00519CE0) or the enemy's (0x0050C280). With the Use / NoChange
 * cursor the cursor is just set again; otherwise each released button (+0x6C +0x66C) finishes the pending action
 * (+0x9C): 2 a move (0x00500DB0), 5 / 4 an attack (0x00503D20 shot or 0x00504400 blow, 0x0050E2D0, 0x00508BA0 and
 * 0x00504D70 / 0x00504B40), 4 with a spell (+0x158) its target: the AI's spell (+0x28C clear: Intelligence lowered by
 * the spell's cost 0x005088D0, the target troop +0xB0 or none), a teleport's departure (+0x28D clear: the flashes
 * +0x29C dropped, the units put at the target) or arrival (CalcRadius, the radius 0x0051DD70, a spTeleport1 flash
 * on each unit, teleport_in.wav). Then the mouse ray (0x00507670) picks: the visible units sorted by distance
 * (+0xC4 / +0xC8 and the obstacles +0xCC / +0xD0, 0x005084E0 / 0x005085E0), the nearest hit obstacle (0x00506130)
 * unless a unit is nearer; a unit under the mouse (0x00511BF0, 0x00511C30 when nearer than 0x00613B60) becomes the
 * target (+0xB0, 0x00508C30) with the attack cursor (0x0051DBF0: Arrow / ArrowInactive, +0x1F4 / +0x1F8, +0x1E4 when
 * not an enemy 0x00511A80) or the spell's (+0x1FC / +0x200); else the board cell under the ray (0x00528450,
 * 0x004FCCB0, within +0x40 of +0x7C) gives the unit standing there or the move cursor (+0x1EC / +0x1F0 by
 * +0x64 +0x64) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_50EEF0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_50EEF0;                 /* nScript::Table */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_50EEF0;
typedef struct { char *u; float d; } Near_50EEF0;
DECOMP_C void __thiscall sub_0051DA60(void *self);
DECOMP_C void __thiscall sub_0050B9A0(void *self);
DECOMP_C int __cdecl sub_005083E0(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_00519CE0(void *self);
DECOMP_C void __cdecl sub_0050C280(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_00443460(void *self, void *name);
DECOMP_C void __thiscall sub_00503D20(void *self, unsigned int a, void *b);
DECOMP_C void __thiscall sub_00504400(void *self, void *unit, void *target);
DECOMP_C void __thiscall sub_0050E2D0(void *self, void *a1, void *unit, int a3, unsigned char board);
DECOMP_C void __stdcall sub_00508BA0(void *unit, void *troop, int a, Str_50EEF0 s, int b);
DECOMP_C void __thiscall sub_00504D70(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_00504B40(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_00500DB0(void *self, void *unit, unsigned int cell);
DECOMP_C void __thiscall sub_0051F5F0(void *self, void *unit);
DECOMP_C void *__thiscall sub_0057B770(void *t, void *out, const char *key);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void __thiscall sub_0051DD70(void *self, int r);
DECOMP_C void __thiscall sub_004FD920(void *self, void *p);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_004F62C0(void *self);
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C unsigned int __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C void __cdecl sub_0054D350(void *self, unsigned int eax, float rate);
DECOMP_C void *__thiscall sub_005184B0(void *self);
DECOMP_C void *__cdecl sub_0044E7A0(void *name);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C float __thiscall sub_004ED000(void *self);
DECOMP_C void __thiscall sub_00512970(void *self, void *pos);
DECOMP_C void __thiscall sub_0051DC40(void *self, unsigned int cell, int delay);
DECOMP_C void *__thiscall sub_00508770(void *self, Tbl_50EEF0 *out);
DECOMP_C int __thiscall sub_005088D0(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0057D220(void *self, const char *s, unsigned int n, int a);
DECOMP_C void __thiscall sub_00507670(void *self, float *o, float *d);
DECOMP_C void __thiscall sub_005084E0(void *self);
DECOMP_C void __thiscall sub_005085E0(void *self, unsigned int lo, unsigned int hi);
DECOMP_C unsigned char __thiscall sub_00506130(void *self, float *o, float *d);
DECOMP_C unsigned char __cdecl sub_00511BF0(void *self, unsigned int eax, float *o, float *d);
DECOMP_C unsigned char __cdecl sub_00511C30(void *self, unsigned int eax, float *o, float *d);
DECOMP_C void __thiscall sub_0050E550(void *self);
DECOMP_C void __thiscall sub_00508C30(void *self, void *unit);
DECOMP_C void __cdecl sub_0051DA30(void *self, unsigned int eax);
DECOMP_C int __thiscall sub_00511E00(void *self);
DECOMP_C int __thiscall sub_00511A80(void *self);
DECOMP_C char __thiscall sub_0051DBF0(void *self, void *map, int a);
DECOMP_C unsigned char __thiscall sub_00528450(void *self, float ox, float oy, float oz, float dx, float dy, float dz,
                                               float *x, float *z);
DECOMP_C void __thiscall sub_004FCCB0(void *self, unsigned int *cell, float x, float z);
DECOMP_C char d_0060FAC0[], d_00608A6C[], d_0060A468[], d_006CA8F0[], d_006CA8F4[], d_0060FA8B[], d_00613B94[],
    d_00613B8C[], d_00613B7C[], d_00613228[], d_00613214[], d_00613B6C[], d_006C8C3C[], d_00613B64[], d_00613960[],
    d_006C88D4[], d_0061393C[], d_00613B60[], d_00608C28[], d_0060A474[], d_0068AE40[], d_006138BC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vf0_50EEF0)(void *self);
typedef void (__thiscall *vfi_50EEF0)(void *self, int a);
typedef void (__thiscall *vfp_50EEF0)(void *self, void *p);
typedef void (__thiscall *vff_50EEF0)(void *self, float f);
typedef void (__thiscall *vffi_50EEF0)(void *self, float f, int a);
typedef void (__thiscall *vfii_50EEF0)(void *self, int a, int b);
typedef float *(__thiscall *vfr_50EEF0)(void *self);
typedef unsigned char (__thiscall *vfb_50EEF0)(void *self);
typedef unsigned char (__thiscall *vfbp_50EEF0)(void *self, void *p);
typedef void (__thiscall *place_50EEF0)(void *self, void *a, void *pos);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define P(o) (*(void **)(this + (o)))
#define C(o) (*(char **)(this + (o)))
#define U(o) (*(unsigned int *)(this + (o)))
#define F(o) (*(float *)(this + (o)))
#define FL(a) (*(float *)(a))

/* the cursor object (+0x70) shows the cursor at +off */
static void cursor_50EEF0(char *this, int off)
{
    char *c = C(0x70);
    ((vfi_50EEF0)VF(c, 0xe8))(c, *(int *)(this + off));
}

/* vf 50 of the object at 0x006CA8F0 / 0x006CA8F4 */
static void reset_50EEF0(char *g)
{
    char *o = *(char **)g + 4;
    ((vf0_50EEF0)VF(o, 0x50))(o);
}

static void named_50EEF0(char *this, const char *name)
{
    Str_50EEF0 s;
    imp_00607324(&s, name);
    sub_00443460(C(0x70), &s);
    imp_00607330(&s);
}

/* 0x00508BA0 with an empty text */
static void done_50EEF0(void *unit, void *troop, int a, int b)
{
    Str_50EEF0 s;
    imp_00607324(&s, d_0060FA8B);
    sub_00508BA0(unit, troop, a, s, b);
}

/* the selected troop (+0x64) may shoot: AI-free side, both sides' flags +0x72 / +0x7E clear */
static int shoots_50EEF0(char *this)
{
    return C(0x64)[0x48] && this[0x1c8] && !(C(0x6c)[0x72] & 0x80) && !(C(0x6c)[0x7e] & 0x80);
}

/* the attack of the selected troop on the target (+0xB0) */
static void attack_50EEF0(char *this)
{
    if (shoots_50EEF0(this)) {
        sub_00503D20(P(0xd8), U(0x64), P(0xb0));
        sub_0050E2D0(this, P(0x64), P(0xb0), 1, 0);
        done_50EEF0(P(0x64), *(void **)(C(0xb0) + 0x2c8), 1, 0);
        sub_00504D70(P(0xd8), P(0x64), P(0xb0));
    } else {
        sub_00504400(P(0xd8), P(0x64), P(0xb0));
        sub_0050E2D0(this, P(0x64), P(0xb0), 0, 0);
        done_50EEF0(P(0x64), *(void **)(C(0xb0) + 0x2c8), 0, 0);
        sub_00504B40(P(0xd8), P(0x64), P(0xb0));
    }
    cursor_50EEF0(this, 0x1e4);
}

/* each unit of the selected troop put at pos (or at its own place) */
static void place_units_50EEF0(char *this, char *at)
{
    unsigned int i;
    for (i = 0; i < sub_0051DAA0(P(0x64)); i++) {
        char *u = (*(char ***)(C(0x64) + 0x58))[i];
        char *p = at ? at : u;
        sub_00512970(u, ((vfr_50EEF0)VF(p, 0x68))(p));
    }
}

/* a spell's (+0x158) target cursor for the unit +0xB0 */
static void spell_unit_50EEF0(char *this)
{
    char *s = C(0x1c0);
    if (((vfbp_50EEF0)VF(s, 0x68))(s, P(0xb0))) {
        U(0x9c) = 4;
        cursor_50EEF0(this, 0x1fc);
        sub_0051F5F0(*(void **)(C(0xb0) + 0x2c8), P(0xb0));
        s = C(0x1c0);
        ((vf0_50EEF0)VF(s, 0x8c))(s);
    } else {
        U(0x9c) = 0;
        cursor_50EEF0(this, 0x200);
    }
}

/* the attack cursor on the unit +0xB0 (0x00511A80 gave 1) of troop t */
static void attack_cursor_50EEF0(char *this, char *t)
{
    char c;
    c = this[0x1c8] && !(C(0x6c)[0x72] & 0x80) && !(C(0x6c)[0x7e] & 0x80);
    if (!sub_0051DBF0(P(0x64), *(void **)(t + 0x98), c)) {
        U(0x9c) = 0;
        if (C(0x64)[0x48])
            named_50EEF0(this, d_0060A474);
        else
            cursor_50EEF0(this, 0x1f8);
        return;
    }
    if (C(0x64)[0x48] && this[0x1c8] && !(C(0x6c)[0x72] & 0x80) && !(C(0x6c)[0x7e] & 0x80)) {
        U(0x9c) = 4;
        sub_00503D20(P(0xd8), U(0x64), P(0xb0));
        sub_0050E2D0(this, P(0x64), P(0xb0), 0, 0);
        named_50EEF0(this, d_00608C28);
        return;
    }
    U(0x9c) = 4;
    sub_00504400(P(0xd8), P(0x64), P(0xb0));
    sub_0050E2D0(this, P(0x64), P(0xb0), 1, 0);
    cursor_50EEF0(this, 0x1f4);
}

/* the unit +0xB0 picked: 0x00508C30 and the cursor */
static void picked_50EEF0(char *this)
{
    sub_00508C30(this, P(0xb0));
    if (this[0x158])
        spell_unit_50EEF0(this);
    else if (sub_00511A80(P(0xb0)) != 1) {
        U(0x9c) = 3;
        cursor_50EEF0(this, 0x1e4);
    } else
        attack_cursor_50EEF0(this, *(char **)(C(0xb0) + 0x2c8));
}

/* the visible object o with its squared distance from the camera (+0x74 +0x44) into the list at +arr */
static void near_50EEF0(char *this, char *o, int arr)
{
    float *c = (float *)(C(0x74) + 0x44), *p, dx, dy, dz;
    unsigned int n = U(arr + 4);
    p = ((vfr_50EEF0)VF(o, 0x68))(o);
    dx = p[0] - c[0];
    dy = p[1] - c[1];
    dz = p[2] - c[2];
    (*(Near_50EEF0 **)(this + arr))[n].u = o;
    (*(Near_50EEF0 **)(this + arr))[n].d = (float)(dx * dx + dy * dy + dz * dz);
    U(arr + 4)++;
}

static void sort_50EEF0(char *this, int list)
{
    unsigned int n = U(list + 8);
    if (n > 0x26)
        sub_005085E0(this + list, 0, n - 1);
    else
        sub_005084E0(this + list);
}

/* the AI's spell is cast: Intelligence lowered, the target troop (or none) */
static void ai_spell_50EEF0(char *this)
{
    char *t = C(0x64);
    unsigned int i;
    this[0x158] = 0;
    for (i = 0; i < *(unsigned int *)(t + 0x5c); i++) {
        Tbl_50EEF0 tb;
        double v;
        int k;
        sub_00508770((*(void ***)(t + 0x58))[i], &tb);
        v = sub_0057AD40(&tb, d_00613960);
        k = sub_005088D0(P(0x1c0));
        sub_0057BC80(&tb, d_00613960, (float)(v - (double)k));
        sub_004220A0(&tb);
    }
    P(0xbc) = P(0xb0);
    if (P(0xb0)) {
        P(0xb8) = *(void **)(C(0xb0) + 0x2c8);
        sub_0051F5F0(P(0xb8), P(0xb0));
        place_units_50EEF0(this, C(0xb0));
        done_50EEF0(P(0x64), *(void **)(C(0xb0) + 0x2c8), 0, 1);
        P(0xb0) = 0;
    } else {
        sub_0057D220(*(void **)d_006C88D4, d_0061393C, 0x23, 0);
        place_units_50EEF0(this, 0);
        done_50EEF0(P(0x64), 0, 0, 1);
    }
    ((vf0_50EEF0)VF(C(0x1c0), 0x70))(C(0x1c0));
    reset_50EEF0(d_006CA8F0);
    U(0x98) = 9;
}

/* the teleport's departure: the flashes dropped, the units put at the target */
static void teleport_out_50EEF0(char *this)
{
    char *f = C(0x29c), *s;
    ((vf0_50EEF0)VF(f, 0x18))(f);
    f = C(0x29c) ? C(0x29c) + 0x18 : 0;
    s = (char *)sub_005184B0(P(0x48));
    ((vfp_50EEF0)VF(s, 0x10))(s, f);
    P(0x29c) = 0;
    this[0x28d] = 1;
    {
        unsigned int i;
        for (i = 0; i < sub_0051DAA0(P(0x64)); i++) {
            char *m = **(char ***)(C(0xb8) + 0x58);
            char *u = (*(char ***)(C(0x64) + 0x58))[i];
            sub_00512970(u, ((vfr_50EEF0)VF(m, 0x68))(m));
        }
    }
    done_50EEF0(P(0x64), P(0xb8), 0, 1);
    ((vf0_50EEF0)VF(C(0x1c0), 0x70))(C(0x1c0));
    sub_0051DC40(P(0xb8), U(0xac), (int)(long long)sub_0057AD40(this + 0x290, d_00613B64));
    reset_50EEF0(d_006CA8F0);
    reset_50EEF0(d_006CA8F4);
    U(0x98) = 9;
    this[0x28c] = 0;
    this[0x158] = 0;
}

/* the teleport's arrival: CalcRadius, the radius and a flash on each unit, teleport_in.wav */
static void teleport_in_50EEF0(char *this)
{
    char *b = C(0xb0), *s;
    void *mem;
    unsigned int i;
    this[0x28d] = 0;
    P(0xbc) = b;
    P(0xb8) = *(void **)(b + 0x2c8);
    sub_0051F5F0(P(0xb8), b);
    {
        Tmp_50EEF0 fn, res;
        void *f;
        P(0xb0) = 0;
        f = sub_0057B770(this + 0x290, &fn, d_00613B94);
        sub_0057A180(f, &res, 0);
        sub_00427820(&res);
        sub_004378D0(&fn);
    }
    sub_0051DD70(P(0xb8), (int)(long long)sub_0057AD40(this + 0x290, d_00613B8C));
    reset_50EEF0(d_006CA8F0);
    {
        char *o = *(char **)d_006CA8F4 + 4;
        ((vfi_50EEF0)VF(o, 0x28))(o, *(int *)(this + 0x2a0));
    }
    sub_004FD920(*(char **)d_006CA8F4 + 4, C(0xb8) + 0x60);
    U(0x98) = 0;
    mem = sub_005E3EAE(0x50);
    P(0x29c) = mem ? sub_004F62C0(mem) : 0;
    for (i = 0; i < sub_0051DAA0(P(0xb8)); i++) {
        char *ps, *u;
        void *pos;
        mem = sub_005E3EAE(0x690);
        if (mem) {
            Str_50EEF0 e;
            imp_00607324(&e, d_0060FA8B);
            ps = (char *)sub_00550420(mem, &e, 0, 0);
            imp_00607330(&e);
        } else
            ps = 0;
        {
            Str_50EEF0 n;
            imp_00607324(&n, d_00613B7C);
            sub_0054EA10(ps, &n);
            imp_00607330(&n);
        }
        sub_0054D350(ps, sub_0054FE30(ps, 0, 0.0f), FL(d_00613228));
        ((vf0_50EEF0)VF(ps, 0x4c))(ps);
        sub_0054FE30(ps, 0, 0.0f);
        ((vff_50EEF0)VF(ps, 4))(ps, FL(d_00613214));
        u = (*(char ***)(C(0xb8) + 0x58))[i];
        pos = ((vfr_50EEF0)VF(u, 0x68))(u);
        ((place_50EEF0)*(void **)(ps + 0x2f4))(*(void **)(ps + 0x2f8), ps + 0x2e4, pos);
        *(unsigned int *)(ps + 0x58) = *(unsigned int *)(ps + 0x64);
        *(unsigned int *)(ps + 0x5c) = *(unsigned int *)(ps + 0x68);
        *(unsigned int *)(ps + 0x60) = *(unsigned int *)(ps + 0x6c);
        *(float *)(ps + 0x64) = 0.0f;
        *(float *)(ps + 0x68) = 0.0f;
        *(float *)(ps + 0x6c) = 0.0f;
        ps[0x70] = 1;
        ((vfp_50EEF0)VF(C(0x29c), 4))(C(0x29c), ps);
    }
    {
        char *f = C(0x29c) ? C(0x29c) + 0x18 : 0;
        s = (char *)sub_005184B0(P(0x48));
        ((vfp_50EEF0)VF(s, 4))(s, f);
    }
    {
        Str_50EEF0 w;
        void *snd;
        char *g;
        imp_00607324(&w, d_00613B6C);
        snd = sub_0044E7A0(&w);
        *(void **)(sub_0042F160() + 0x48) = snd;
        imp_00607330(&w);
        g = *(char **)(sub_0042F160() + 0x48);
        ((vffi_50EEF0)VF(g, 0x18))(g, sub_004ED000(*(void **)d_006C8C3C), 0);
        g = *(char **)(sub_0042F160() + 0x48);
        ((vfii_50EEF0)VF(g, 0xc))(g, 1, 0);
    }
}

DECOMP(0050EEF0)
void __thiscall f_0050EEF0(void *self)
{
    char *this = (char *)self;
    unsigned char hit = 0;
    float o[3], d[3];

    if (F(0x284) >= FL(d_0060FAC0))
        return;
    {
        char *w = C(0x48), *h = *(char **)(w + 0x44);
        if (h && --*(int *)(h + 8) == 0)
            ((vfi_50EEF0)VF(h + 4, 0))(h + 4, 1);
        *(void **)(w + 0x44) = 0;
    }
    if (P(0x210)) {
        sub_0051DA60(P(0x210));
        P(0x210) = 0;
    }
    {
        unsigned char *keys = *(unsigned char **)(C(0x6c) + 0x660);
        unsigned int n = *(unsigned int *)(C(0x6c) + 0x664), i;
        for (i = 0; i < n; i++) {
            unsigned char side;
            if (keys[i * 2 + 1] != 1)
                continue;
            side = keys[i * 2];
            if (side == (unsigned char)this[0x95])
                sub_0050B9A0(this);
            else if (side == 1) {
                if (!(unsigned char)sub_005083E0(this, 0))
                    sub_00519CE0(P(0x48));
            } else if (side && side == (unsigned char)this[0x94])
                sub_0050C280(this, 0);
        }
    }
    if (imp_006071E4(C(0x70) + 0x23c, d_00608A6C) || imp_006071E4(C(0x70) + 0x23c, d_0060A468)) {
        sub_00443460(C(0x70), C(0x70) + 0x23c);
        return;
    }
    {
        int *up = *(int **)(C(0x6c) + 0x66c);
        unsigned int n = *(unsigned int *)(C(0x6c) + 0x670), i;
        for (i = 0; i < n; i++) {
            if (up[i] != 0)
                continue;
            switch (U(0x9c)) {
            case 2:
                reset_50EEF0(d_006CA8F0);
                sub_00500DB0(P(0xd8), P(0x64), U(0xac));
                cursor_50EEF0(this, 0x1e4);
                P(0xb0) = 0;
                U(0x98) = 3;
                return;
            case 5:
                reset_50EEF0(d_006CA8F0);
                attack_50EEF0(this);
                P(0xb0) = 0;
                U(0x98) = 4;
                return;
            case 4:
                if (!this[0x158]) {
                    if (!P(0xb0)) {
                        U(0x9c) = 0;
                        U(0x98) = 0;
                        return;
                    }
                    attack_50EEF0(this);
                    U(0x98) = 4;
                    P(0xb0) = 0;
                    reset_50EEF0(d_006CA8F0);
                    return;
                }
                if (!this[0x28c]) {
                    ai_spell_50EEF0(this);
                    return;
                }
                if (!this[0x28d])
                    teleport_out_50EEF0(this);
                else
                    teleport_in_50EEF0(this);
                break;
            }
        }
    }
    P(0xb0) = 0;
    sub_00507670(this, o, d);
    if (!this[0x28c] || this[0x28d]) {
        char *best = 0;
        float bestd = 0.0f;
        unsigned int i;
        int g;
        U(0xc8) = 0;
        U(0xd4) = 0;
        for (g = 0; g < 2; g++) {
            unsigned int *grp = (unsigned int *)(this + 0x54 + g * 0xc), j;
            for (j = 0; j < grp[0]; j++) {
                unsigned int k;
                for (k = 0; k < *(unsigned int *)((char *)(size_t)grp[-1] + j * 0xc8 + 0x5c); k++) {
                    char *u = (*(char ***)((char *)(size_t)grp[-1] + j * 0xc8 + 0x58))[k];
                    if (((vfb_50EEF0)VF(u, 0x6c))(u))
                        near_50EEF0(this, u, 0xc4);
                }
            }
        }
        sort_50EEF0(this, 0xc0);
        {
            char **it;
            for (it = *(char ***)(this + 0x1d8); it != *(char ***)(this + 0x1dc); it++) {
                char *ob = *it;
                if (((vfb_50EEF0)VF(ob, 0x6c))(ob))
                    near_50EEF0(this, ob, 0xd0);
            }
        }
        sort_50EEF0(this, 0xcc);
        for (i = 0; i < U(0xd4); i++) {
            Near_50EEF0 *e = *(Near_50EEF0 **)(this + 0xd0) + i;
            if (*(int *)(e->u + 0x1d8) == 0 && sub_00506130(e->u, o, d)) {
                e = *(Near_50EEF0 **)(this + 0xd0) + i;
                bestd = e->d;
                best = e->u;
                break;
            }
        }
        for (i = 0; i < U(0xc8); i++) {
            Near_50EEF0 *e = *(Near_50EEF0 **)(this + 0xc4) + i;
            if (!sub_00511BF0(e->u, (unsigned int)(size_t)e, o, d))
                continue;
            e = *(Near_50EEF0 **)(this + 0xc4) + i;
            if (FL(d_00613B60) > e->d && !sub_00511C30(e->u, (unsigned int)(size_t)e, o, d))
                continue;
            if (best && (*(Near_50EEF0 **)(this + 0xc4))[i].d > bestd) {
                P(0xb4) = best;
                sub_0050E550(this);
                sub_00508C30(this, P(0xb0));
                return;
            }
            P(0xb0) = (*(Near_50EEF0 **)(this + 0xc4))[i].u;
            P(0x210) = *(void **)(C(0xb0) + 0x2c8);
            sub_0051DA30(P(0x210), U(0x210));
            hit = 1;
            if (sub_00511E00(P(0xb0)) != 0) {
                picked_50EEF0(this);
                return;
            }
        }
        if (best) {
            P(0xb4) = best;
            sub_0050E550(this);
            sub_00508C30(this, P(0xb0));
            return;
        }
    }
    if (sub_00528450(P(0x44), o[0], o[1], o[2], d[0], d[1], d[2], (float *)(this + 0xa0), (float *)(this + 0xa8))) {
        float dz = F(0xa8) - F(0x84), dx = F(0xa0) - F(0x7c);
        float dist = (float)(dx * dx + 0.0f * 0.0f + dz * dz);
        if (F(0x40) > dist) {
            unsigned int cell;
            char *map = C(0x3c), *u;
            sub_004FCCB0(map, &cell, F(0xa0), F(0xa8));
            U(0xac) = cell;
            map = C(0x3c);
            if (cell < *(unsigned int *)(map + 0x7c) &&
                (u = *(char **)(*(char **)(map + 0x68) + cell * 0x10 + 0xc)) != 0 && !this[0x28c]) {
                P(0xb0) = u;
                P(0x210) = *(void **)(u + 0x2c8);
                sub_0051DA30(P(0x210), cell);
                if (this[0x158])
                    spell_unit_50EEF0(this);
                else {
                    char *t = *(char **)(u + 0x2c8);
                    if (sub_00511A80(u) != 1) {
                        U(0x9c) = 3;
                        cursor_50EEF0(this, 0x1e4);
                    } else
                        attack_cursor_50EEF0(this, t);
                }
                return;
            }
            if (this[0x158]) {
                if (this[0x28c] && !this[0x28d]) {
                    if ((*(char **)(C(0xb8) + 0x64))[cell]) {
                        U(0x9c) = 4;
                        cursor_50EEF0(this, 0x1fc);
                    } else {
                        U(0x9c) = 0;
                        cursor_50EEF0(this, 0x200);
                    }
                    return;
                }
                {
                    float pos[3];
                    char *s = C(0x1c0);
                    pos[0] = F(0xa0);
                    pos[1] = 0.0f;
                    pos[2] = F(0xa8);
                    if (((vfbp_50EEF0)VF(s, 0x6c))(s, pos)) {
                        U(0x9c) = 4;
                        cursor_50EEF0(this, 0x1fc);
                    } else {
                        U(0x9c) = 0;
                        cursor_50EEF0(this, 0x200);
                    }
                }
                return;
            }
            if ((*(char **)(C(0x64) + 0x64))[cell]) {
                cursor_50EEF0(this, 0x1ec);
                U(0x9c) = 2;
            } else {
                cursor_50EEF0(this, 0x1f0);
                U(0x9c) = 0;
            }
            if (!hit) {
                F(0x1cc) = FL(d_0068AE40);
                F(0x1d0) = FL(d_006138BC);
            }
            return;
        }
    }
    if (!hit) {
        F(0x1cc) = FL(d_0068AE40);
        F(0x1d0) = FL(d_006138BC);
    }
    if (this[0x158]) {
        cursor_50EEF0(this, 0x200);
        U(0x9c) = 0;
    } else {
        cursor_50EEF0(this, 0x1e4);
        U(0x9c) = 0;
    }
}
