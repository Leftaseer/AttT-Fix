/* 0x00549C10: Lua unit method Dead: flags +0x2FC; Unit[name (+8)].Animation.Death (0x004323E0, 0x0045C740,
 * 0x004648E0, 0x004B2690, 0x0044C0E0) becomes a new "creature" animation (0x004CB990, size 0x24) stored under
 * "Death" in the animation map (+0x200, 0x00443DD0, refcounted), which then becomes the current one (+0x1FC, reset by
 * 0x004CAFE0(0)) and is set to its last frame; the target (+0x2D8) is dropped, the state (+0x2D4) is 9, the unit
 * leaves the selection list (0x006C8C3C, 0x004F5E40) when +0x304, its state name (+0x1D0) is "Dead", vf18 runs, and
 * the box corners (+0x258..+0x284) relative to the position (+0x64) through the matrix (+0x168) give +0x74/+0x7C
 * (0x004F6B30) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_549C10;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_549C10;                 /* nScript::Table */
typedef struct { void *tbl; Str_549C10 key; } Ref_549C10;
typedef struct { Tbl_549C10 t; const char *k; } RefC_549C10;
typedef struct { float x, y, z; } V3_549C10;
typedef struct { float m[16]; } M44_549C10;
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_549C10 *__thiscall sub_0045C740(void *self, Ref_549C10 *out, Str_549C10 key);
DECOMP_C RefC_549C10 *__thiscall sub_004648E0(void *self, RefC_549C10 *out, const char *key);
DECOMP_C RefC_549C10 *__thiscall sub_004B2690(void *self, RefC_549C10 *out, const char *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_00548AC0(void *self);
DECOMP_C void __thiscall sub_004EF350(void *self, unsigned int n, void *val);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void *__thiscall sub_004CB990(void *self, void *anim, Str_549C10 kind, void *owner, void *name);
DECOMP_C void **__thiscall sub_00443DD0(void *self, void *key);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C void __thiscall sub_004F5E40(void *list, void *unit);
DECOMP_C void __cdecl sub_004F6B30(float *corners, V3_549C10 org, M44_549C10 m, float *o1, float *o2, float *o3);
DECOMP_C char d_00613DC8[], d_0060C138[], d_0060C088[], d_0060FA8B[], d_0060FF34[], d_0061B478[], d_006C8C3C[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *rel_549C10)(void *self, int flag);
typedef void (__thiscall *vf_549C10)(void *self);

static void unref_549C10(unsigned int *o)
{
    if (o && --o[1] == 0)
        ((rel_549C10)(*(void ***)o)[0])(o, 1);
}

DECOMP(00549C10)
int __thiscall f_00549C10(char *this, void *L)
{
    Str_549C10 name, kind, empty, key;
    Tbl_549C10 unit, t, anim;
    Ref_549C10 r1;
    RefC_549C10 r2, r3;
    unsigned int val, *obj;
    void *mem, **slot;
    float corners[12], o1, o2, o3;
    V3_549C10 org;
    int i;

    *(this + 0x2fc) = 1;
    imp_00607334(&name, this + 8);
    sub_0044C0E0(sub_004B2690(sub_004648E0(sub_0045C740(sub_004323E0(&unit, d_0060C088), &r1, name), &r2,
                                           d_0060C138), &r3, d_00613DC8), &t);
    sub_00435D90(&anim, &t);
    sub_004220A0(&t);
    sub_004220A0(&r3.t);
    sub_004220A0(&r2.t);
    imp_00607330(&r1.key);
    sub_004220A0(&unit);

    sub_00548AC0(this + 0x204);
    val = *(unsigned int *)(this + 0x208);
    sub_004EF350(this + 0x210, 9, &val);
    *(int *)(this + 0x220) = 1;
    *(int *)(this + 0x224) = 1;

    mem = sub_005E3EAE(0x24);
    obj = 0;
    if (mem) {
        imp_00607324(&empty, d_0060FA8B);
        imp_00607324(&kind, d_0060FF34);
        obj = sub_004CB990(mem, &anim, kind, this + 0x1f8, &empty);
    }
    imp_00607324(&key, d_00613DC8);
    slot = sub_00443DD0(this + 0x200, &key);
    if (obj)
        obj[1]++;
    unref_549C10(*slot);
    *slot = obj;
    imp_00607330(&key);
    if (mem)
        imp_00607330(&empty);

    imp_00607324(&key, d_00613DC8);
    *(void **)(this + 0x1fc) = *sub_00443DD0(this + 0x200, &key);
    imp_00607330(&key);
    sub_004CAFE0(*(void **)(this + 0x1fc), 0);
    {
        char *m = *(char **)(this + 0x1f8);
        int last = *(int *)(*(char **)(m + 0x1c4) + 0x1c8) - 1;
        *(int *)(m + 0x1cc) = last;
        *(int *)(*(char **)(m + 0x1c4) + 0x1d8) = last;
    }
    unref_549C10(*(unsigned int **)(this + 0x2d8));
    *(void **)(this + 0x2d8) = 0;
    *(int *)(this + 0x2d4) = 9;
    if (*(this + 0x304)) {
        sub_004F5E40(*(void **)d_006C8C3C, this);
        *(this + 0x304) = 0;
    }
    imp_006072F8(this + 0x1d0, d_0061B478);
    ((vf_549C10)(*(void ***)this)[0x18 / 4])(this);

    for (i = 0; i < 12; i++)
        corners[i] = *(float *)(this + 0x258 + i * 4) - *(float *)(this + 0x64 + (i % 3) * 4);
    org.x = 0.0f;
    org.y = 0.0f;
    org.z = 0.0f;
    sub_004F6B30(corners, org, *(M44_549C10 *)(this + 0x168), &o1, &o2, &o3);
    *(float *)(this + 0x74) = o1;
    *(float *)(this + 0x7c) = o2;
    *(this + 0x80) = 1;
    *(this + 0x305) = 1;
    sub_004220A0(&anim);
    return 0;
}
