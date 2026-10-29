/* 0x00574050: nSpell::Regeneration vf28 (start): the effect of this spell's name (+8) on the target (+0x64) is
 * stopped (0x0051E730, its vf74 with an event, 0x0051E6B0), for "spA06_Snapgoat" on every unit (200 bytes each) of
 * the battle's list too; the spell registers itself (0x0051EDD0); the target unit's (+0xA4) position and model height
 * go to Lua as CurStandardInfo (0x005608D0); the script SpellAct[name] becomes +0x70 and its "Begin" is called (its
 * boolean result kept); the "PSMesh" and "PSDetMesh" particle meshes (0x00573FB0, 0x00571AA0, size 0x58) placed at
 * height 2*h + 3 + 6*(+0xB4 - 1) become +0x7C / +0x80 (refcounted); a callback node (0x61D468, method 0x005724E0)
 * is pushed on the target's list (+0x18); +0x68 is MainObjectTable.QnTurn (default 3); vf74 with an event when
 * Begin returned true. Returns what 0x004220A0 returns */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_574050;                 /* std::string */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_574050;
DECOMP_C void *__thiscall sub_0051E730(void *self, void *name);
DECOMP_C void __thiscall sub_0051E6B0(void *self, void *eff);
DECOMP_C char *__cdecl sub_00432260(void);
DECOMP_C void __thiscall sub_0051EDD0(void *self, void *spell);
DECOMP_C void __cdecl sub_005608D0(const char *code, unsigned int len);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00437870(void *self, void *out, void *name);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C char *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C int __cdecl sub_00402C20(void *L, int idx);                /* lua_type */
DECOMP_C int __cdecl sub_00402EA0(void *L, int idx);                /* lua_toboolean */
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__thiscall sub_00573FB0(void *self, void *name);
DECOMP_C unsigned int *__thiscall sub_00571AA0(void *self, void *mesh, void *unit, float *pos, void *scene);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C float __thiscall sub_0057AED0(void *self, const char *key, float def);
DECOMP_C char d_0060AC14[], d_0061D58C[], d_0061D520[], d_00613988[], d_006121B8[], d_008D122C[], d_0061D1D0[],
    d_0061D1C4[], d_0061D468[], d_005724E0[], d_0061D1B4[], d_0061D584[], d_006097EC[];
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *ev_574050)(void *self, void *ev);
typedef char *(__thiscall *box_574050)(void *self);
typedef void (__thiscall *rel_574050)(void *self, int flag);

static void stop_574050(void *list, void *name)
{
    void *e = sub_0051E730(list, name);
    if (e) {
        void *ev = d_0060AC14;
        ((ev_574050)(*(void ***)e)[0x74 / 4])(e, &ev);
        sub_0051E6B0(list, e);
    }
}

static float height_574050(void *m)
{
    double top = *(float *)(((box_574050)(*(void ***)m)[0xec / 4])(m) + 0x34);
    return (float)(top - *(float *)(((box_574050)(*(void ***)m)[0xec / 4])(m) + 4));
}

static void mesh_574050(char *this, void **slot, const char *kind, float *pos)
{
    void *mem = sub_005E3EAE(0x58);
    unsigned int *o = 0, *old;
    if (mem) {
        char *g = sub_0042F160();
        void *scene = *(char **)(g + 0x5c) ? *(char **)(g + 0x5c) + 4 : 0;
        Str_574050 s;
        imp_00607324(&s, kind);
        o = sub_00571AA0(mem, sub_00573FB0(this, &s), *(void **)(*(char **)(this + 0x64) + 0xa4), pos, scene);
        if (o)
            o[1]++;
        old = *slot;
        if (old && --old[1] == 0)
            ((rel_574050)(*(void ***)old)[0])(old, 1);
        *slot = o;
        imp_00607330(&s);
        return;
    }
    old = *slot;
    if (old && --old[1] == 0)
        ((rel_574050)(*(void ***)old)[0])(old, 1);
    *slot = 0;
}

DECOMP(00574050)
int __thiscall f_00574050(char *this)
{
    char *unit, *res, buf[0x430];
    Tmp_574050 act, tmp, fn;
    void **q, **node, *m, *ev;
    float pos[3], h;
    unsigned int k;
    char ok;

    stop_574050(*(void **)(this + 0x64), this + 8);
    if (imp_006071E4(this + 8, d_0061D58C)) {
        char *p = *(char **)(sub_00432260() + 0xbc);
        int i;
        for (i = 0; i < *(int *)(p + 0x54); i++)
            stop_574050(*(char **)(p + 0x50) + i * 200, this + 8);
    }
    sub_0051EDD0(*(void **)(this + 0x64), this);

    unit = *(char **)(*(char **)(this + 0x64) + 0xa4);
    h = height_574050(*(void **)(unit + 0x1e8));
    imp_006073D0(buf, d_0061D520, (double)*(float *)(unit + 0x64), (double)*(float *)(unit + 0x68),
                 (double)*(float *)(unit + 0x6c), (double)h);
    sub_005608D0(buf, __builtin_strlen(buf));

    sub_004323E0(&act, d_00613988);
    sub_0057A860(this + 0x70, sub_00437870(&act, &tmp, this + 8));
    sub_004220A0(&tmp);
    sub_0057B770(this + 0x70, &fn, d_006121B8);
    res = sub_0057A180(&fn, &tmp, 1);
    ok = 0;
    if (*(int *)(res + 0xc) >= 1 && sub_00402C20(*(void **)d_008D122C, *(int *)(res + 0x10) + 1))
        ok = sub_00402EA0(*(void **)d_008D122C, *(int *)(res + 0x10) + 1) != 0;
    sub_00427820(&tmp);

    h = height_574050(*(void **)(unit + 0x1e8));
    k = (*(int *)(*(char **)(this + 0x64) + 0xb4) * 3 - 3) * 2;
    pos[0] = 0.0f;
    pos[2] = 0.0f;
    pos[1] = (float)((double)h + h + 3.0 + (double)k);
    mesh_574050(this, (void **)(this + 0x7c), d_0061D1D0, pos);
    mesh_574050(this, (void **)(this + 0x80), d_0061D1C4, pos);

    q = (void **)(*(char **)(this + 0x64) + 0x18);
    node = sub_005E3EAE(0x10);
    if (node) {
        node[1] = *q;
        node[0] = d_0061D468;
        node[2] = this;
        node[3] = d_005724E0;
    }
    *q = node;

    m = sub_0057B4E0(this + 0x70, &tmp, d_0061D1B4);
    *(int *)(this + 0x68) = (int)(long long)sub_0057AED0(m, d_0061D584, *(float *)d_006097EC);
    sub_004220A0(&tmp);
    if (ok) {
        ev = d_0060AC14;
        ((ev_574050)(*(void ***)this)[0x74 / 4])(this, &ev);
    }
    sub_004378D0(&fn);
    return sub_004220A0(&act);
}
