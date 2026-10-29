/* 0x00505B30: the battle army layout's constructor (the battle's sides arg 1, arg 2 passed to 0x005056C0): its vtable,
 * 87 slots (+0x0C, 16 bytes: 1000, 0), two empty lists (+0x60C / +0x618), the script table TacticLevel.OffsUnit
 * (+0x624, 0x0057A860); lays the units out (0x00505330, 0x005056C0, which takes EBX, here 4 in its low byte as the
 * original leaves it), then every unit of both sides' groups (+0x04 groups of 0xC8 bytes, +0x08 of them; units +0x58,
 * +0x5C of them) faces its heading +0x78 give or take up to 20 (rand, 0x004ACB80 at once) and is scaled at random
 * (0x004F6550: x and z between 0x00613748 and 0x0061374C, y between 0x00613740 and 0x00613744, steps of 100); the
 * first unit of the first group keeps scale 0x00608A70. Returns this */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_00505330(void *self);
DECOMP_C void __cdecl sub_005056C0(void *self, unsigned int ebx, void *a);
DECOMP_C void __thiscall sub_004ACB80(void *self, float angle, int speed);
DECOMP_C float __cdecl sub_004F6550(float lo, float hi, float steps);
DECOMP_C char d_006136C8[], d_00613600[], d_00607CC4[], d_0060AB58[], d_00613750[], d_00608B4C[], d_00613748[],
    d_0061374C[], d_00613740[], d_00613744[], d_00608A70[];
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");

#define UNIT(side, g, u) (*(char ***)(*(char **)(*(char **)(s + 8) + (side) + 4) + (g) * 0xc8 + 0x58))[u]
#define F(a) (*(float *)(a))

DECOMP(00505B30)
void *__thiscall f_00505B30(void *this, char *sides, void *a2)
{
    char *s = (char *)this, *u;
    unsigned int t1[3], t2[3], i, g, side;
    struct { void *tbl; const char *key; } p;
    float base, v;
    int r;
    *(int *)(s + 4) = 0;
    *(void **)s = d_006136C8;
    for (i = 0; i < 0x57; i++) {
        *(int *)(s + 0xc + i * 16 + 4) = 0;
        *(int *)(s + 0xc + i * 16) = 1000;
    }
    *(void **)(s + 0x60c) = d_00613600;
    *(int *)(s + 0x610) = 0;
    *(int *)(s + 0x614) = 0;
    *(void **)(s + 0x618) = d_00613600;
    *(int *)(s + 0x61c) = 0;
    *(int *)(s + 0x620) = 0;
    *(int *)(s + 0x628) = 0;
    *(void **)(s + 0x624) = d_00607CC4;
    *(int *)(s + 0x62c) = -1;
    *(char **)(s + 8) = sides;
    p.tbl = sub_004323E0(t1, d_0060AB58);
    p.key = d_00613750;
    sub_004369F0(&p, t2);
    sub_0057A860(s + 0x624, t2);
    sub_004220A0(t2);
    sub_004220A0(t1);
    sub_00505330(this);
    sub_005056C0(this, 4, a2);
    for (side = 0; side < 0x18; side += 0xc)
        for (g = 0; g < *(unsigned int *)(*(char **)(s + 8) + side + 8); g++)
            for (i = 0; i < *(unsigned int *)(*(char **)(*(char **)(s + 8) + side + 4) + g * 0xc8 + 0x5c); i++) {
                u = UNIT(side, g, i);
                base = F(u + 0x78);
                r = imp_00607400() % 40 - 20;
                sub_004ACB80(u, (float)(r + base), 1);
                v = sub_004F6550(F(d_00613748), F(d_0061374C), F(d_00608B4C));
                u = UNIT(side, g, i);
                F(u + 0x98) = v;
                u[0xa4] = 1;
                v = sub_004F6550(F(d_00613748), F(d_0061374C), F(d_00608B4C));
                u = UNIT(side, g, i);
                F(u + 0xa0) = v;
                u[0xa4] = 1;
                v = sub_004F6550(F(d_00613740), F(d_00613744), F(d_00608B4C));
                u = UNIT(side, g, i);
                F(u + 0x9c) = v;
                u[0xa4] = 1;
            }
    u = UNIT(0, 0, 0);
    *(unsigned int *)(u + 0x98) = *(unsigned int *)d_00608A70;
    *(unsigned int *)(u + 0x9c) = *(unsigned int *)d_00608A70;
    *(unsigned int *)(u + 0xa0) = *(unsigned int *)d_00608A70;
    u[0xa4] = 1;
    return this;
}
