/* 0x005384B0: TownAnims::TownAnims (script table, arg 2): the scriptable object base "TownsAnim" (0x005B3FD0 with arg
 * 2), its interface (+0x1F4) and model holder (+0x1F8, 0x004B8640) with their vtables, three empty refcounted slots
 * (+0x200..+0x208) and +0x20C (0x00432D70); the table is kept (+0x1E8), its "Effect" applied (0x00463B40 -> 0x004AB810),
 * its "Pos" (x, y with default 0, z) becomes the position (+0x64, the previous one at +0x58) and +0x1C4, its "Rot" the
 * heading (+0x78), the scale 0x00608A70; a new 0x24-byte model (0x004CB520 of +0x204) fills +0x200, 0x00537B70 builds
 * it, a new 0x380-byte part (0x00592020 with the model's vf EC result) fills +0x1A8; outside the world (0x006C88D8
 * +0x40 clear) a new 0x324-byte shadow (0x004EC6F0, "unitToShadow" / "unitsShadow") fills +0x208 and the four
 * script tables (+0x1C4.., refs +0x1CC, +0x1D8, +0x1E4, +0x1F0) are released; registered with 0x006C8C3C
 * (0x004EF750). Returns this */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5384B0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_5384B0;                 /* nScript::Table */
DECOMP_C void __thiscall sub_005B3FD0(void *self, void *name, int a, unsigned int b);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C void __thiscall sub_00432D70(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C float __thiscall sub_0057AE00(void *self, int i, float def);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void *__thiscall sub_004CB520(void *self, void *a);
DECOMP_C void __thiscall sub_00537B70(void *self);
DECOMP_C void *__thiscall sub_00592020(void *self, void *owner, void *a, int b);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_5384B0 s1,
                                       Str_5384B0 s2);
DECOMP_C void __thiscall sub_004EF750(void *self, void *obj, int a, int b);
DECOMP_C void __cdecl sub_00402270(void *L, int t, int ref);        /* luaL_unref */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_00615C1C[], d_0060B900[], d_00615B4C[], d_00615B3C[], d_00615B30[], d_00615B28[], d_0060978C[],
    d_0060BB98[], d_0060B9C0[], d_00608A70[], d_006C88D8[], d_0060C2E8[], d_0060C2D8[], d_008D122C[], d_006C8C3C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *rel_5384B0)(void *self, int del);
typedef void *(__thiscall *get_5384B0)(void *self);

static void put_5384B0(void **slot, void *o)
{
    void *old;
    if (o)
        *(int *)((char *)o + 4) += 1;
    old = *slot;
    if (old && !(*(int *)((char *)old + 4) -= 1))
        ((rel_5384B0)**(void ***)old)(old, 1);
    *slot = o;
}

static void unref_5384B0(char *s, int off)
{
    if (*(int *)(s + off) > 0) {
        sub_00402270(*(void **)d_008D122C, -10000, *(int *)(s + off));   /* LUA_REGISTRYINDEX */
        *(int *)(s + off) = -1;
    }
}

DECOMP(005384B0)
void *__thiscall f_005384B0(void *this, void *tbl, unsigned int a2)
{
    char *s = (char *)this, *m;
    unsigned int str[7];
    struct { void *t; const char *k; } key;
    Tbl_5384B0 tmp, pos;
    float x, y, z;
    void *o;
    imp_00607324(str, d_00615C1C);
    sub_005B3FD0(this, str, 0, a2);
    imp_00607330(str);
    *(void **)(s + 0x1f4) = d_0060B900;
    sub_004B8640(s + 0x1f8, 1);
    *(void **)s = d_00615B4C;
    *(void **)(s + 0x1f4) = d_00615B3C;
    *(void **)(s + 0x1f8) = d_00615B30;
    *(void **)(s + 0x200) = 0;
    *(void **)(s + 0x204) = 0;
    *(void **)(s + 0x208) = 0;
    sub_00432D70(s + 0x20c);
    *(unsigned int *)(s + 0x328) = *(unsigned int *)d_00615B28;
    sub_0057A860(s + 0x1e8, tbl);
    key.t = s + 0x1e8;
    key.k = d_0060978C;
    sub_004AB810(this, sub_00463B40(&key, 0, str), 0);
    imp_00607330(str);
    key.t = s + 0x1e8;
    key.k = d_0060BB98;
    sub_004369F0(&key, &tmp);
    sub_00435D90(&pos, &tmp);
    sub_004220A0(&tmp);
    z = sub_0057AC90(&pos, 3);
    x = sub_0057AC90(&pos, 1);
    y = sub_0057AE00(&pos, 2, 0.0f);
    *(unsigned int *)(s + 0x58) = *(unsigned int *)(s + 0x64);
    *(float *)(s + 0x64) = x;
    *(unsigned int *)(s + 0x5c) = *(unsigned int *)(s + 0x68);
    *(float *)(s + 0x68) = y;
    *(unsigned int *)(s + 0x60) = *(unsigned int *)(s + 0x6c);
    *(float *)(s + 0x6c) = z;
    s[0x70] = 1;
    sub_0057A860(s + 0x1c4, &pos);
    *(float *)(s + 0x78) = sub_0057AD40(s + 0x1e8, d_0060B9C0);
    s[0x80] = 1;
    *(unsigned int *)(s + 0x98) = *(unsigned int *)d_00608A70;
    *(unsigned int *)(s + 0x9c) = *(unsigned int *)d_00608A70;
    *(unsigned int *)(s + 0xa0) = *(unsigned int *)d_00608A70;
    s[0xa4] = 1;
    o = sub_005E3EAE(0x24);
    o = o ? sub_004CB520(o, s + 0x204) : 0;
    put_5384B0((void **)(s + 0x200), o);
    sub_00537B70(this);
    o = sub_005E3EAE(0x380);
    if (o) {
        m = *(char **)(s + 0x204);
        o = sub_00592020(o, this, ((get_5384B0)(*(void ***)m)[0xec / 4])(m), 6);
    }
    put_5384B0((void **)(s + 0x1a8), o);
    if (!(*(char **)d_006C88D8)[0x40]) {
        o = sub_005E3EAE(0x324);
        if (o) {
            Str_5384B0 a, b;
            imp_00607324(&b, d_0060C2E8);
            imp_00607324(&a, d_0060C2D8);
            o = sub_004EC6F0(o, s + 0x204, this, *(unsigned char *)(s + 0x324), a, b);
        }
        put_5384B0((void **)(s + 0x208), o);
        unref_5384B0(s, 0x1cc);
        unref_5384B0(s, 0x1d8);
        unref_5384B0(s, 0x1e4);
        unref_5384B0(s, 0x1f0);
    }
    sub_004EF750(*(void **)d_006C8C3C, this, 0, 0);
    sub_004220A0(&pos);
    return this;
}
