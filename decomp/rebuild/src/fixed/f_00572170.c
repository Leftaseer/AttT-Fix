/* 0x00572170: nSpell::AresSword vf28 (start): the effect of this spell's name (+8) on the target (+0x64) is stopped
 * (0x0051E730, its vf74 with an event, 0x0051E6B0), the spell registers (0x0051EDD0) and +0x6C becomes 2, then the
 * spell is announced (0x00562A50); the SpellAct table (0x00613988, 0x004323E0, 0x00437870) becomes +0x74 (0x0057A860)
 * and its "Begin" (0x0057B770) is called without results (0x0057A180); the "PSMesh" / "PSDetMesh" particle meshes
 * (0x005720D0 names them, 0x00571AA0, size 0x58) placed at height 2*(+0xB4) + 11 (0x0061D1D8) become +0x80 / +0x84
 * (refcounted); callback nodes (vftable 0x0061D014) are pushed on the target's +8 list (0x00571DA0), the global list
 * 0x006CA8E0 (0x00575AD0) and the target's +0x18 list (0x005724E0). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[0x30 / 4]; } Tmp_572170;
DECOMP_C void *__thiscall sub_0051E730(void *self, void *name);
DECOMP_C void __thiscall sub_0051E6B0(void *self, void *eff);
DECOMP_C void __thiscall sub_0051EDD0(void *self, void *spell);
DECOMP_C void __cdecl sub_00562A50(void *name);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00437870(void *self, void *out, void *name);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *key);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int nres);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_005720D0(void *self, void *name);
DECOMP_C void *__thiscall sub_00571AA0(void *self, void *mesh, void *unit, float *pos, void *scene);
DECOMP_C char d_0060AC14[], d_00613988[], d_006121B8[], d_0061D1D0[], d_0061D1C4[], d_0061D014[], d_006CA8E0[],
    d_00571DA0[], d_00575AD0[], d_005724E0[], d_0061D1D8[], d_0068AE08[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *ev_572170)(void *self, void *ev);
typedef void (__thiscall *rel_572170)(void *self, int flag);

static void stop_572170(void *list, void *name)
{
    void *e = sub_0051E730(list, name);
    if (e) {
        void *ev = d_0060AC14;
        ((ev_572170)(*(void ***)e)[0x74 / 4])(e, &ev);
        sub_0051E6B0(list, e);
    }
}

static void release_572170(void *o)
{
    if (o && !--((unsigned int *)o)[1])
        ((rel_572170)(*(void ***)o)[0])(o, 1);
}

static void mesh_572170(char *this, void **slot, const char *kind, float *pos)
{
    void *mem = sub_005E3EAE(0x58);
    void *o = 0, *old;
    if (mem) {
        char *g = sub_0042F160();
        void *scene = *(char **)(g + 0x5c) ? *(char **)(g + 0x5c) + 4 : 0;
        unsigned int name[7];
        imp_00607324(name, kind);
        o = sub_00571AA0(mem, sub_005720D0(this, name), *(void **)(*(char **)(this + 0x64) + 0xa4), pos, scene);
        if (o)
            ((unsigned int *)o)[1]++;
        old = *slot;
        release_572170(old);
        *slot = o;
        imp_00607330(name);
        return;
    }
    old = *slot;
    release_572170(old);
    *slot = 0;
}

static void push_572170(void **head, char *spell, void *fn)
{
    void **node = sub_005E3EAE(0x10);
    if (node) {
        node[1] = *head;
        node[0] = d_0061D014;
        node[2] = spell;
        node[3] = fn;
    }
    *head = node;
}

DECOMP(00572170)
void __thiscall f_00572170(char *this)
{
    char *target = *(char **)(this + 0x64);
    Tmp_572170 act, tmp, fn;
    float pos[3];

    stop_572170(target, this + 8);
    sub_0051EDD0(target, this);
    *(int *)(this + 0x6c) = 2;
    sub_00562A50(this + 8);

    sub_004323E0(&act, d_00613988);
    sub_0057A860(this + 0x74, sub_00437870(&act, &tmp, this + 8));
    sub_004220A0(&tmp);
    sub_0057B770(this + 0x74, &fn, d_006121B8);
    sub_0057A180(&fn, &tmp, 0);
    sub_00427820(&tmp);

    {
        unsigned int n = *(unsigned int *)(target + 0xb4);
        pos[0] = 0.0f;
        pos[2] = 0.0f;
        pos[1] = (float)((double)n + (double)n + *(double *)d_0061D1D8);
    }
    mesh_572170(this, (void **)(this + 0x80), d_0061D1D0, pos);
    mesh_572170(this, (void **)(this + 0x84), d_0061D1C4, pos);

    push_572170((void **)(target + 8), this, d_00571DA0);
    push_572170((void **)d_006CA8E0, this, d_00575AD0);
    push_572170((void **)(target + 0x18), this, d_005724E0);
    sub_004378D0(&fn);
    sub_004220A0(&act);
}
