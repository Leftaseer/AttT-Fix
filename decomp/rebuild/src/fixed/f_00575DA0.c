/* 0x00575DA0: nSpell::Target vf28 (start): the effect of this spell's name (+8) on the target (+0x64) is stopped
 * (0x0051E730, its vf74 with an event, 0x0051E6B0), the spell registers (0x0051EDD0) and +0x6C becomes 3; the
 * target's +0xA8 gains 100.0 (0x00609648) and the spell is announced (0x00562A50); Spell.Spell[name] (0x005608F0,
 * 0x00561830) replaces +0x70 (refcounted) and its "Begin" (0x005626D0) is called (0x0055F400); the "PSMesh" and
 * "PSDetMesh" particle meshes (0x00575B80 names them, 0x00571AA0, size 0x58) placed at height 2*(+0xB4) + 11
 * (0x0061D1D8) become +0x74 / +0x78 (refcounted); callback nodes (vftable 0x0061D734) are pushed, one with 0x00575AD0
 * on the global list 0x006CA8E0 and one with 0x005724E0 on the target's list (+0x18). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_575DA0;                 /* std::string */
DECOMP_C void *__thiscall sub_0051E730(void *self, void *name);
DECOMP_C void __thiscall sub_0051E6B0(void *self, void *eff);
DECOMP_C void __thiscall sub_0051EDD0(void *self, void *spell);
DECOMP_C void __cdecl sub_00562A50(void *name);
DECOMP_C void *__cdecl sub_005608F0(void);
DECOMP_C void *__thiscall sub_00561830(void *self, void *name);
DECOMP_C void *__thiscall sub_005626D0(void *self, void *name);
DECOMP_C int __fastcall sub_0055F400(void *fn);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_00575B80(void *self, void *name);
DECOMP_C void *__thiscall sub_00571AA0(void *self, void *mesh, void *unit, float *pos, void *scene);
DECOMP_C char d_0060AC14[], d_00611738[], d_006121B8[], d_0061D1D0[], d_0061D1C4[], d_0061D734[], d_006CA8E0[],
    d_00575AD0[], d_005724E0[], d_00609648[], d_0061D1D8[], d_0068AE08[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *ev_575DA0)(void *self, void *ev);
typedef void (__thiscall *rel_575DA0)(void *self, int flag);

static void stop_575DA0(void *list, void *name)
{
    void *e = sub_0051E730(list, name);
    if (e) {
        void *ev = d_0060AC14;
        ((ev_575DA0)(*(void ***)e)[0x74 / 4])(e, &ev);
        sub_0051E6B0(list, e);
    }
}

static void *keep_575DA0(void *o)
{
    if (o)
        ((unsigned int *)o)[1]++;
    return o;
}

static void release_575DA0(void *o)
{
    if (o && !--((unsigned int *)o)[1])
        ((rel_575DA0)(*(void ***)o)[0])(o, 1);
}

static void mesh_575DA0(char *this, void **slot, const char *kind, float *pos)
{
    void *mem = sub_005E3EAE(0x58);
    void *o = 0, *old;
    if (mem) {
        char *g = sub_0042F160();
        void *scene = *(char **)(g + 0x5c) ? *(char **)(g + 0x5c) + 4 : 0;
        Str_575DA0 s;
        imp_00607324(&s, kind);
        o = sub_00571AA0(mem, sub_00575B80(this, &s), *(void **)(*(char **)(this + 0x64) + 0xa4), pos, scene);
        if (o)
            ((unsigned int *)o)[1]++;
        release_575DA0(*slot);
        *slot = o;
        imp_00607330(&s);
        return;
    }
    release_575DA0(*slot);
    *slot = 0;
}

static void push_575DA0(void **head, char *spell, void *fn)
{
    void **node = sub_005E3EAE(0x10);
    if (node) {
        node[1] = *head;
        node[0] = d_0061D734;
        node[2] = spell;
        node[3] = fn;
    }
    *head = node;
}

DECOMP(00575DA0)
void __thiscall f_00575DA0(char *this)
{
    char *target = *(char **)(this + 0x64);
    Str_575DA0 s, begin;
    void *spell, *inst, *fn;
    float pos[3];

    stop_575DA0(target, this + 8);
    sub_0051EDD0(target, this);
    *(int *)(this + 0x6c) = 3;
    *(float *)(target + 0xa8) = (float)((double)*(float *)(target + 0xa8) + *(double *)d_00609648);
    sub_00562A50(this + 8);

    imp_00607324(&s, d_00611738);
    spell = keep_575DA0(sub_00561830(sub_005608F0(), &s));
    imp_00607330(&s);
    inst = keep_575DA0(sub_00561830(spell, this + 8));
    release_575DA0(*(void **)(this + 0x70));
    *(void **)(this + 0x70) = inst;

    imp_00607324(&begin, d_006121B8);
    fn = keep_575DA0(sub_005626D0(inst, &begin));
    imp_00607330(&begin);
    sub_0055F400(fn);

    {
        unsigned int n = *(unsigned int *)(target + 0xb4);
        pos[0] = 0.0f;
        pos[2] = 0.0f;
        pos[1] = (float)((double)n + (double)n + *(double *)d_0061D1D8);
    }
    mesh_575DA0(this, (void **)(this + 0x74), d_0061D1D0, pos);
    mesh_575DA0(this, (void **)(this + 0x78), d_0061D1C4, pos);

    push_575DA0((void **)d_006CA8E0, this, d_00575AD0);
    push_575DA0((void **)(target + 0x18), this, d_005724E0);
    release_575DA0(fn);
    release_575DA0(spell);
}
