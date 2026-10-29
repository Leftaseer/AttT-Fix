/* 0x00449440: a world army's update (dt): while active (+0x74) and within 0x006C8C08 (squared, horizontally) of the
 * camera (0x006CA2C4): an aggressive army (+0x76) that reaches the hero (0x00425F60 vf68) within its radius (+0x70)
 * starts the battle: the script's WorldLevel.Armys entry for its name (+0x08, 0x00449340 / 0x004491F0) becomes
 * TacticLevel.armyWhoAttack (0x0057BF50) and the world's +0x70 starts the battle (0x0053D4A0(1)); within the radius
 * plus 0x0060AB40 its creatures (+0x60 list) flee once (0x00549550, +0x77), farther away they return (0x005495D0).
 * When its circle is in view (0x00458090 on the frustum 0x006CA2C8, whose EAX input only passes through) it is shown
 * (+0x75) and its creatures update (vf04 with dt); out of range or view it is hidden. Returns what the original
 * leaves in EAX on the update path (the last creature's result), else the frustum test's EAX or 0 where the original leaves junk */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_449440;
typedef struct { unsigned int t[3]; Str_449440 s; } Pair_449440;
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C void *__thiscall sub_00449340(void *self, void *out, Str_449440 name);
DECOMP_C void __thiscall sub_004491F0(void *self, void *out);
DECOMP_C void __thiscall sub_004491A0(void *self);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0057BF50(void *self, const char *key, void *val);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void __thiscall sub_0053D4A0(void *self, int a);
DECOMP_C void __thiscall sub_00549550(void *self);
DECOMP_C void __thiscall sub_005495D0(void *self);
DECOMP_C unsigned int __cdecl sub_00458090(void *self, unsigned int eax, float x, float z, float r);
DECOMP_C char d_006CA2C4[], d_006C8C08[], d_0060AB6C[], d_0060AB64[], d_0060AB58[], d_0060AB48[], d_0060AB40[],
    d_006CA2C8[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
typedef float *(__thiscall *pos_449440)(void *self);
typedef int (__thiscall *upd_449440)(void *self, float dt);

#define F(o) (*(float *)(s + (o)))

static void each_449440(char *s, void (__thiscall *f)(void *))
{
    char **head = *(char ***)(s + 0x60), **n;
    for (n = (char **)head[0]; n != head; n = (char **)n[0])
        f(n[2]);
}

DECOMP(00449440)
int __thiscall f_00449440(void *this, float dt)
{
    char *s = (char *)this, *cam, *h1, *h2;
    float dx, dz, d2, hx, hz, r, r2;
    int res = 0;
    if (!s[0x74])
        return 0;
    cam = *(char **)d_006CA2C4;
    dx = F(0x68) - *(float *)(cam + 0x44);
    dz = F(0x6c) - *(float *)(cam + 0x4c);
    d2 = dz * dz + dx * dx;
    if (!(*(float *)d_006C8C08 > d2)) {
        s[0x75] = 0;
        return 0;
    }
    if (s[0x76]) {
        h1 = sub_00425F60();
        h2 = sub_00425F60();
        hz = ((pos_449440)(*(void ***)h1)[0x68 / 4])(h1)[2];
        hx = ((pos_449440)(*(void ***)h2)[0x68 / 4])(h2)[0];
        r = F(0x70);
        dx = F(0x68) - hx;
        dz = F(0x6c) - hz;
        d2 = dz * dz + dx * dx;
        r2 = r * r;
        if (!(r2 < d2)) {
            unsigned int a[3], t[3], c[3], d[3];
            Pair_449440 b;
            Str_449440 name;
            struct { void *tbl; const char *key; } p;
            imp_00607334(&name, s + 8);
            p.tbl = sub_004323E0(a, d_0060AB6C);
            p.key = d_0060AB64;
            sub_004491F0(sub_00449340(&p, &b, name), t);
            sub_00435D90(c, t);
            sub_004220A0(t);
            sub_004491A0(&b);
            sub_004220A0(a);
            sub_0057BF50(sub_004323E0(d, d_0060AB58), d_0060AB48, c);
            sub_004220A0(d);
            sub_0053D4A0(*(void **)(sub_0042F160() + 0x70), 1);
            sub_004220A0(c);
        } else {
            r = (float)(r + *(double *)d_0060AB40);
            r2 = r * r;
            if (!(r2 < d2)) {
                if (!s[0x77]) {
                    each_449440(s, sub_00549550);
                    s[0x77] = 1;
                }
            } else if (s[0x77]) {
                each_449440(s, sub_005495D0);
                s[0x77] = 0;
            }
        }
    }
    res = (int)sub_00458090(*(void **)d_006CA2C8, 0, F(0x68), F(0x6c), F(0x70));
    if (!(char)res) {
        s[0x75] = 0;
        return res;
    }
    s[0x75] = 1;
    {
        char **head = *(char ***)(s + 0x60), **n;
        for (n = (char **)head[0]; n != head; n = (char **)n[0]) {
            void **c = (void **)n[2];
            res = ((upd_449440)(*(void ***)c)[1])(c, dt);
        }
    }
    return res;
}
