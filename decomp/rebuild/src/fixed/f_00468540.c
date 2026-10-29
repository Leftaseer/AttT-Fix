/* 0x00468540: adds a companion creature (arg 1 its description) to the hero's formation: the formation box from the
 * script table +0x48's "Forming" ("w" halved, "h"), a new 0x2D4-byte CWorldHeroCreature (0x00539C70), told its home
 * (+0x6C, 0x005398C0) when arg 2, listed (+0x58 vf04) and placed (0x00538B50) at a random offset (0x004F6550: across
 * -w/2..w/2, along 0..h, steps of 100) from the hero's position (0x00425F60 vf68) or, while the hero rides
 * (+0x4E4), from +0x5C, at the heading +0x68; it faces away from the leader (+0x54: _CIatan2 of the offset, plus
 * 0x006095F0 when x is negative, times 0x00609628 into +0x78) and joins the list +0x2C. Returns what the original
 * leaves in EAX */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void *__thiscall sub_00539C70(void *self, void *desc);
DECOMP_C void __thiscall sub_005398C0(void *self, void *home);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C float __cdecl sub_004F6550(float lo, float hi, float steps);
DECOMP_C void __thiscall sub_00538B50(void *self, void *off, void *pos, float heading);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C double decomp_CIatan2(double y, double x);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_0060C42C[], d_0068A734[], d_0060C428[], d_00607CE0[], d_00608088[], d_00608B4C[], d_006095F0[],
    d_00609628[];
typedef void (__thiscall *add_468540)(void *self, void *item);
typedef float *(__thiscall *pos_468540)(void *self);

DECOMP(00468540)
int __thiscall f_00468540(void *this, void *desc, unsigned char home)
{
    char *s = (char *)this, *h, **head, **nn;
    struct { void *tbl; const char *key; } p;
    unsigned int t0[3], t[3];
    float r, a, u, v, off[3], *p1, *p2, dx, dz, ang;
    void *c, **l;
    p.tbl = s + 0x48;
    p.key = d_0060C42C;
    sub_004369F0(&p, t0);
    sub_00435D90(t, t0);
    sub_004220A0(t0);
    r = (float)(sub_0057AD40(t, d_0068A734) * *(double *)d_00607CE0);
    a = sub_0057AD40(t, d_0060C428);
    c = sub_005E3EAE(0x2d4);
    c = c ? sub_00539C70(c, desc) : 0;
    if (home)
        sub_005398C0(c, s + 0x6c);
    l = *(void ***)(s + 0x58);
    ((add_468540)(*(void ***)l)[1])(l, c);
    h = sub_00425F60();
    if (h[0x4e4]) {
        u = sub_004F6550(*(float *)d_00608088 - r, r, *(float *)d_00608B4C);
        v = sub_004F6550(0.0f, a, *(float *)d_00608B4C);
        off[0] = u, off[1] = 0.0f, off[2] = v;
        sub_00538B50(c, off, s + 0x5c, *(float *)(s + 0x68));
    } else {
        h = sub_00425F60();
        u = sub_004F6550(*(float *)d_00608088 - r, r, *(float *)d_00608B4C);
        v = sub_004F6550(0.0f, a, *(float *)d_00608B4C);
        off[0] = u, off[1] = 0.0f, off[2] = v;
        sub_00538B50(c, off, ((pos_468540)(*(void ***)h)[0x68 / 4])(h), *(float *)(s + 0x68));
    }
    l = *(void ***)(s + 0x54);
    p1 = ((pos_468540)(*(void ***)l)[0x68 / 4])(l);
    p2 = ((pos_468540)(*(void ***)c)[0x68 / 4])(c);
    dx = p2[0] - p1[0];
    dz = p2[2] - p1[2];
    if (0.0f > dx)
        ang = (float)((float)decomp_CIatan2(dx, dz) + *(double *)d_006095F0);
    else
        ang = (float)decomp_CIatan2(dx, dz);
    ((char *)c)[0x80] = 1;
    *(float *)((char *)c + 0x78) = (float)(ang * *(double *)d_00609628);
    head = *(char ***)(s + 0x30);
    nn = sub_005AD6C0(head, (char **)head[1], &c);
    sub_004E0EF0(s + 0x2c, 1);
    head[1] = (char *)nn;
    *(char ***)nn[1] = nn;
    return sub_004220A0(t);
}
