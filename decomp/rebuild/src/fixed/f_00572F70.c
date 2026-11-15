/* 0x00572F70: nSpell::Invisible vf28 (start): the effect of this spell's name (+8) on the target (+0x64) is stopped
 * (0x0051E730, its vf74 with an event, 0x0051E6B0), the spell registers (0x0051EDD0) and +0x68 becomes 3; the
 * target's +0xA8 loses 1000.0 (0x0068AE10) and the spell is announced (0x00562A50); Spell.Spell[name] (0x005608F0,
 * 0x00561830) replaces +0x74 (refcounted) and its "Begin" (0x005626D0) is called (0x0055F400); for every unit of the
 * target's list (+0x58 / +0x5C) a "PSMesh" particle mesh (0x00572D40 names it, 0x00571AA0, size 0x58) is created half
 * the unit's height above it (0x00511CD0 * 0.5, 0x00607CE0) and takes the place of the same entry of this spell's
 * +0x7C array (refcounted); a callback node (vftable 0x61D2B4, method 0x005745F0) is pushed on the global list
 * 0x6CA8E0. */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_572F70;                 /* std::string */
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
DECOMP_C float __thiscall sub_00511CD0(void *self);
DECOMP_C void *__thiscall sub_00572D40(void *self, int i);
DECOMP_C void *__thiscall sub_00571AA0(void *self, void *mesh, void *unit, float *pos, void *scene);
DECOMP_C char d_0060AC14[], d_00611738[], d_006121B8[], d_0061D2B4[], d_006CA8E0[], d_005745F0[],
    d_0068AE10[], d_00607CE0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *ev_572F70)(void *self, void *ev);
typedef void (__thiscall *rel_572F70)(void *self, int flag);

static void stop_572F70(void *list, void *name)
{
    void *e = sub_0051E730(list, name);
    if (e) {
        void *ev = d_0060AC14;
        ((ev_572F70)(*(void ***)e)[0x74 / 4])(e, &ev);
        sub_0051E6B0(list, e);
    }
}

static void *keep_572F70(void *o)
{
    if (o)
        ((unsigned int *)o)[1]++;
    return o;
}

static void release_572F70(void *o)
{
    if (o && !--((unsigned int *)o)[1])
        ((rel_572F70)(*(void ***)o)[0])(o, 1);
}

static float height_572F70(void *unit)
{
    return (float)((double)sub_00511CD0(unit) * *(double *)d_00607CE0);
}

static void mesh_572F70(char *this, void *unit, int i)
{
    void *mem = sub_005E3EAE(0x58);
    void **slot = (void **)(*(char **)(this + 0x7c) + i * 4);
    void *o = 0, *old;
    if (mem) {
        char *g = sub_0042F160();
        void *scene = *(char **)(g + 0x5c) ? *(char **)(g + 0x5c) + 4 : 0;
        float pos[3];
        pos[0] = 0.0f;
        pos[2] = 0.0f;
        pos[1] = height_572F70(unit);
        o = sub_00571AA0(mem, sub_00572D40(this, i + 1), unit, pos, scene);
        if (o)
            ((unsigned int *)o)[1]++;
        release_572F70(*slot);
        *slot = o;
        return;
    }
    release_572F70(*slot);
    *slot = 0;
}

static void push_572F70(char *spell)
{
    void **node = sub_005E3EAE(0x10);
    if (node) {
        node[1] = *(void **)d_006CA8E0;
        node[0] = d_0061D2B4;
        node[2] = spell;
        node[3] = d_005745F0;
    }
    *(void **)d_006CA8E0 = node;
}

DECOMP(00572F70)
void __thiscall f_00572F70(char *this)
{
    char *target = *(char **)(this + 0x64);
    Str_572F70 s, begin;
    void *spell, *inst, *fn;
    int i;

    stop_572F70(target, this + 8);
    sub_0051EDD0(target, this);
    *(int *)(this + 0x68) = 3;
    *(float *)(target + 0xa8) = (float)((double)*(float *)(target + 0xa8) - *(double *)d_0068AE10);
    sub_00562A50(this + 8);

    imp_00607324(&s, d_00611738);
    spell = keep_572F70(sub_00561830(sub_005608F0(), &s));
    imp_00607330(&s);
    inst = keep_572F70(sub_00561830(spell, this + 8));
    release_572F70(*(void **)(this + 0x74));
    *(void **)(this + 0x74) = inst;

    imp_00607324(&begin, d_006121B8);
    fn = keep_572F70(sub_005626D0(inst, &begin));
    imp_00607330(&begin);
    sub_0055F400(fn);

    for (i = 0; i < *(int *)(target + 0x5c); i++)
        mesh_572F70(this, *(void **)(*(char **)(target + 0x58) + i * 4), i);

    push_572F70(this);
    release_572F70(fn);
    release_572F70(spell);
}
