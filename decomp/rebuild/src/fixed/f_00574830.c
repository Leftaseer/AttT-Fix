/* 0x00574830: nSpell::Slow vf28 (start): the effect of this spell's name (+8) on the target (+0x64) is stopped
 * (0x0051E730, its vf74 with an event, 0x0051E6B0), the spell registers (0x0051EDD0) and +0x68 becomes 3; the target
 * unit's (+0xA4) position and model height go to the scripts as CurStandardInfo (0x005608D0), the spell is announced
 * (0x00562A50), Spell.Spell[name] (0x005608F0, 0x00561830) replaces +0x74 (refcounted) and its "Begin" (0x005626D0) is
 * called (0x0055F400); the "PSMesh" / "PSDetMesh" particle meshes (0x00574610, 0x00571AA0, size 0x58) at height
 * 2*(+0xB4) + 11 become +0x78 / +0x7C (refcounted); two callback nodes (vftable 0x61D5A0) are pushed, one with
 * 0x005745F0 on the global list 0x6CA8E0 and one with 0x005724E0 on the target's list (+0x18). */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_574830;                 /* std::string */
typedef struct { void *vt, *next; char *self; void *fn; } Node_574830;
DECOMP_C void *__thiscall sub_0051E730(void *self, void *name);
DECOMP_C void __thiscall sub_0051E6B0(void *self, void *eff);
DECOMP_C void __thiscall sub_0051EDD0(void *self, void *spell);
DECOMP_C void __cdecl sub_005608D0(const char *code, unsigned int len);
DECOMP_C void __cdecl sub_00562A50(void *name);
DECOMP_C void *__cdecl sub_005608F0(void);
DECOMP_C void *__thiscall sub_00561830(void *self, void *name);
DECOMP_C void *__thiscall sub_005626D0(void *self, void *name);
DECOMP_C int __fastcall sub_0055F400(void *fn);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_00574610(void *self, void *name);     /* mesh table entry */
DECOMP_C void *__thiscall sub_00571AA0(void *self, void *mesh, void *unit, float *pos, void *scene);
DECOMP_C char d_0060AC14[], d_0061D520[], d_0061D1D0[], d_0061D1C4[], d_00611738[], d_006121B8[], d_0061D5A0[],
    d_006CA8E0[], d_005724E0[], d_005745F0[];
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *ev_574830)(void *self, void *ev);
typedef char *(__thiscall *box_574830)(void *self);
typedef void (__thiscall *rel_574830)(void *self, int flag);

static void stop_574830(void *list, void *name)
{
    void *e = sub_0051E730(list, name);
    if (e) {
        void *ev = d_0060AC14;
        ((ev_574830)(*(void ***)e)[0x74 / 4])(e, &ev);
        sub_0051E6B0(list, e);
    }
}

static float height_574830(void *m)
{
    double top = *(float *)(((box_574830)(*(void ***)m)[0xec / 4])(m) + 0x34);
    return (float)(top - *(float *)(((box_574830)(*(void ***)m)[0xec / 4])(m) + 4));
}

static void *keep_574830(void *o)
{
    if (o)
        ((unsigned int *)o)[1]++;
    return o;
}

static void release_574830(void *o)
{
    if (o && !--((unsigned int *)o)[1])
        ((rel_574830)(*(void ***)o)[0])(o, 1);
}

static void mesh_574830(char *this, void **slot, const char *kind, void *unit, float *pos)
{
    void *mem = sub_005E3EAE(0x58);
    void *o = 0, *old;
    if (mem) {
        char *g = sub_0042F160();
        void *scene = *(char **)(g + 0x5c) ? *(char **)(g + 0x5c) + 4 : 0;
        Str_574830 s;
        imp_00607324(&s, kind);
        o = sub_00571AA0(mem, sub_00574610(this, &s), unit, pos, scene);
        if (o)
            ((unsigned int *)o)[1]++;
        old = *slot;
        if (old && !--((unsigned int *)old)[1])
            ((rel_574830)(*(void ***)old)[0])(old, 1);
        *slot = o;
        imp_00607330(&s);
        return;
    }
    old = *slot;
    if (old && !--((unsigned int *)old)[1])
        ((rel_574830)(*(void ***)old)[0])(old, 1);
    *slot = 0;
}

static void push_574830(void **head, char *spell, void *fn)
{
    Node_574830 *node = sub_005E3EAE(0x10);
    if (node) {
        node->next = *head;
        node->vt = d_0061D5A0;
        node->self = spell;
        node->fn = fn;
    }
    *head = node;
}

DECOMP(00574830)
void __thiscall f_00574830(char *this)
{
    char *target = *(char **)(this + 0x64);
    char *unit, buf[0x430];
    Str_574830 s, begin;
    void *spell, *inst, *fn;
    float pos[3];
    unsigned int n;

    stop_574830(target, this + 8);
    sub_0051EDD0(target, this);
    *(int *)(this + 0x68) = 3;

    unit = *(char **)(target + 0xa4);
    {
        float h = height_574830(*(void **)(unit + 0x1e8));
        imp_006073D0(buf, d_0061D520, (double)*(float *)(unit + 0x64), (double)*(float *)(unit + 0x68),
                     (double)*(float *)(unit + 0x6c), (double)h);
    }
    sub_005608D0(buf, __builtin_strlen(buf));
    sub_00562A50(this + 8);

    imp_00607324(&s, d_00611738);
    spell = keep_574830(sub_00561830(sub_005608F0(), &s));
    imp_00607330(&s);
    inst = keep_574830(sub_00561830(spell, this + 8));
    release_574830(*(void **)(this + 0x74));
    *(void **)(this + 0x74) = inst;

    imp_00607324(&begin, d_006121B8);
    fn = keep_574830(sub_005626D0(*(void **)(this + 0x74), &begin));
    imp_00607330(&begin);
    sub_0055F400(fn);

    n = *(unsigned int *)(target + 0xb4);
    pos[0] = 0.0f;
    pos[2] = 0.0f;
    pos[1] = (float)((double)n + (double)n + 11.0);
    mesh_574830(this, (void **)(this + 0x78), d_0061D1D0, unit, pos);
    mesh_574830(this, (void **)(this + 0x7c), d_0061D1C4, unit, pos);

    push_574830((void **)d_006CA8E0, this, d_005745F0);
    push_574830((void **)(target + 0x18), this, d_005724E0);

    release_574830(fn);
    release_574830(spell);
}
