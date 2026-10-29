/* 0x005B6370: the world map's grass (patch p of the 3x3 around the hero; with reset the fade distance +0x338 is
 * started from the camera's tilt): the hero's (or with the map view, the camera's) tile (+0x2E4 / +0x2E8 wide from
 * +0x30C / +0x308); when the hero has moved one tile along x or z the eight neighbour patches' blades (+0x340, the
 * world copies +0x364, 0x10 each) and counts (+0x3AC, four per patch) are shifted, then all patches are marked to be
 * replanted (+0x445..+0x44D) and the tiles (+0x4C..+0x90) set around the new one (+0x2DD). The patch's translation
 * (+0x94, from its tile unless +0x44E) moves its blades (0x005B809E); a patch to replant puts each blade on the
 * ground (0x00473110), hidden (0x0068AE40) unless 0x005B4F60 says it grows there, each quarter sorted by 0x005B4EE0
 * and counted. The tiles' visibility (+0x43C, 0x00457F80 against +0x48) is set, then each counted blade fades by its
 * squared distance from the camera (the nearest kept at +0x338) in four bands of +0x334. Returns 0 */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */
DECOMP_C float *__stdcall sub_005B803E(float *out, float x, float y, float z);        /* D3DXMatrixTranslation */
DECOMP_C float *__stdcall sub_005B809E(void *out, unsigned ostride, const void *v, unsigned vstride,
                                      const void *m, unsigned n);                     /* D3DXVec3TransformCoordArray */
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C unsigned char __thiscall sub_005B4F60(void *self, float *pt);
DECOMP_C unsigned char __cdecl sub_00457F80(void *self, unsigned int eax, float x, float y, float z, float r);
DECOMP_C char d_0060AB40[], d_00609B68[], d_0068AE40[], d_005B4EE0[], d_00609E08[], d_0060ACC0[], d_00607CE0[],
    d_0060A170[], d_0061BFA8[], d_00620BA8[];
DECOMP_C void (__cdecl *imp_qsort)(void *, unsigned int, unsigned int, void *) __asm__("__imp__qsort");
typedef float *(__thiscall *vfr_5B6370)(void *self);

#define U(o) (*(unsigned int *)(this + (o)))
#define I(o) (*(int *)(this + (o)))
#define F(o) (*(float *)(this + (o)))
#define C(o) (*(char **)(this + (o)))
#define D(a) (*(double *)(a))
#define MC(d, s) sub_005E4232(*(void **)(this + (d)), *(void **)(this + (s)), U(0x320) << 4)
/* blade k of patch p (0x10 each) and its world copy (0xC each) */
#define BLADE(p, k) ((float *)(C(0x340 + (p) * 4) + (k) * 0x10))
#define WORLD(p, k) ((float *)(C(0x364 + (p) * 4) + (k) * 0xc))

/* blade k put on the ground; shown (and counted) where it grows */
static void plant_5B6370(char *this, int p, int k, int *count)
{
    float *v = WORLD(p, k), pt[3];
    BLADE(p, k)[1] = sub_00473110(C(0x2c), v[0], v[2]);
    BLADE(p, k)[3] = 0.0f;
    v = WORLD(p, k);
    pt[0] = v[0];
    pt[1] = 0.0f;
    pt[2] = v[2];
    if (sub_005B4F60(this, pt)) {
        BLADE(p, k)[3] = 0.0f;
        (*count)++;
    } else
        BLADE(p, k)[3] = *(float *)d_0068AE40;
}

/* blade k's fade by its squared distance from the camera */
static void fade_5B6370(char *this, int p, int k, const float *cam, double a, double b, double c)
{
    float *v, dx, dy, dz, d;
    WORLD(p, k)[1] = BLADE(p, k)[1];
    v = WORLD(p, k);
    dx = cam[0] - v[0];
    dy = cam[1] - v[1];
    dz = cam[2] - v[2];
    d = (float)(dx * dx + dy * dy + dz * dz);
    if (F(0x338) > d)
        F(0x338) = d;
    if (a > d)
        BLADE(p, k)[3] = (float)(1.0 - (F(0x338) + d) / F(0x334));
    else if (b > d)
        BLADE(p, k)[3] = (float)(1.0 - (F(0x338) + d) / F(0x334) - D(d_0060A170));
    if (d >= b && c > d)
        BLADE(p, k)[3] = (float)(1.0 - (F(0x338) + d) / F(0x334) - D(d_0061BFA8));
    if (d > c)
        BLADE(p, k)[3] = (float)(1.0 - (d + F(0x338)) / F(0x334) - D(d_00620BA8));
}

DECOMP(005B6370)
int __thiscall f_005B6370(void *self, int p, char reset)
{
    char *this = (char *)self;
    char *hero = sub_00425F60(), *c;
    float pos[3], cam[3];
    int i, j, k;

    if (!(*(char **)(sub_0042F160() + 0x70))[0x3ad]) {
        float *h = ((vfr_5B6370)(*(void ***)hero)[0x68 / 4])(hero);
        pos[0] = h[0];
        pos[1] = h[1];
        pos[2] = h[2];
    } else {
        c = sub_00424E70();
        pos[0] = *(float *)(c + 0x50);
        pos[1] = *(float *)(c + 0x54);
        pos[2] = *(float *)(c + 0x58);
    }
    c = sub_00424E70();
    cam[0] = *(float *)(c + 0x44);
    cam[1] = *(float *)(c + 0x48);
    cam[2] = *(float *)(c + 0x4c);
    if (reset) {
        float t1 = *(float *)(sub_00424E70() + 0x68), t2 = *(float *)(sub_00424E70() + 0x68);
        F(0x338) = (float)((D(d_0060AB40) - t2) * (D(d_0060AB40) - t1) * D(d_00609B68));
    } else
        F(0x338) = 0.0f;
    i = (int)(long long)((long double)(pos[0] - F(0x30c)) / (long double)I(0x2e4));
    j = (int)(long long)((long double)(F(0x308) - pos[2]) / (long double)I(0x2e8));
    if (p == 0 && i == I(0x4c) && j == I(0x50))
        this[0x2dd] = 0;
    if (this[0x44e])
        this[0x2dd] = 1;
    else if (p == 0 && (i != I(0x4c) || j != I(0x50))) {
        int dx = i - I(0x4c), dz = j - I(0x50);
        U(0x445) = 0;
        U(0x449) = 0;
        this[0x44d] = 0;
        if (dx > 0 && dz == 0) {
            MC(0x344, 0x348);
            MC(0x350, 0x340);
            MC(0x358, 0x35c);
            MC(0x348, 0x34c);
            MC(0x340, 0x354);
            MC(0x35c, 0x360);
            U(0x3bc) = U(0x3cc);
            U(0x3c0) = U(0x3d0);
            U(0x3c4) = U(0x3d4);
            U(0x3ec) = U(0x3ac);
            U(0x3c8) = U(0x3d8);
            U(0x3f0) = U(0x3b0);
            U(0x3f4) = U(0x3b4);
            U(0x40c) = U(0x41c);
            U(0x3f8) = U(0x3b8);
            U(0x410) = U(0x420);
            U(0x414) = U(0x424);
            U(0x3cc) = U(0x3dc);
            U(0x418) = U(0x428);
            U(0x3d0) = U(0x3e0);
            U(0x3d4) = U(0x3e4);
            U(0x3d8) = U(0x3e8);
            U(0x3ac) = U(0x3fc);
            U(0x3b0) = U(0x400);
            U(0x41c) = U(0x42c);
            U(0x3b4) = U(0x404);
            U(0x3b8) = U(0x408);
            U(0x420) = U(0x430);
            U(0x424) = U(0x434);
            U(0x428) = U(0x438);
            this[0x448] = 1;
            this[0x44a] = 1;
            this[0x44c] = 1;
        }
        if (dx < 0 && dz == 0) {
            MC(0x34c, 0x348);
            MC(0x354, 0x340);
            MC(0x360, 0x35c);
            MC(0x348, 0x344);
            MC(0x340, 0x350);
            MC(0x35c, 0x358);
            U(0x3dc) = U(0x3cc);
            U(0x3e0) = U(0x3d0);
            U(0x3e4) = U(0x3d4);
            U(0x3fc) = U(0x3ac);
            U(0x3e8) = U(0x3d8);
            U(0x400) = U(0x3b0);
            U(0x404) = U(0x3b4);
            U(0x42c) = U(0x41c);
            U(0x408) = U(0x3b8);
            U(0x430) = U(0x420);
            U(0x434) = U(0x424);
            U(0x3cc) = U(0x3bc);
            U(0x438) = U(0x428);
            U(0x3d0) = U(0x3c0);
            U(0x3d4) = U(0x3c4);
            U(0x3d8) = U(0x3c8);
            U(0x3ac) = U(0x3ec);
            U(0x3b0) = U(0x3f0);
            U(0x3b4) = U(0x3f4);
            U(0x41c) = U(0x40c);
            U(0x3b8) = U(0x3f8);
            U(0x420) = U(0x410);
            U(0x424) = U(0x414);
            U(0x428) = U(0x418);
            this[0x446] = 1;
            this[0x449] = 1;
            this[0x44b] = 1;
        } else if (dz < 0 && dx == 0) {
            MC(0x358, 0x350);
            MC(0x35c, 0x340);
            MC(0x360, 0x354);
            MC(0x350, 0x344);
            MC(0x340, 0x348);
            MC(0x354, 0x34c);
            U(0x40c) = U(0x3ec);
            U(0x410) = U(0x3f0);
            U(0x414) = U(0x3f4);
            U(0x41c) = U(0x3ac);
            U(0x418) = U(0x3f8);
            U(0x420) = U(0x3b0);
            U(0x424) = U(0x3b4);
            U(0x42c) = U(0x3fc);
            U(0x428) = U(0x3b8);
            U(0x430) = U(0x400);
            U(0x434) = U(0x404);
            U(0x3ec) = U(0x3bc);
            U(0x438) = U(0x408);
            U(0x3f0) = U(0x3c0);
            U(0x3f4) = U(0x3c4);
            U(0x3f8) = U(0x3c8);
            U(0x3ac) = U(0x3cc);
            U(0x3b0) = U(0x3d0);
            U(0x3b4) = U(0x3d4);
            U(0x3fc) = U(0x3dc);
            U(0x3b8) = U(0x3d8);
            U(0x400) = U(0x3e0);
            U(0x404) = U(0x3e4);
            U(0x408) = U(0x3e8);
            this[0x446] = 1;
            this[0x447] = 1;
            this[0x448] = 1;
        } else if (dz > 0 && dx == 0) {
            MC(0x344, 0x350);
            MC(0x348, 0x340);
            MC(0x34c, 0x354);
            MC(0x350, 0x358);
            MC(0x340, 0x35c);
            MC(0x354, 0x360);
            U(0x3bc) = U(0x3ec);
            U(0x3c0) = U(0x3f0);
            U(0x3c4) = U(0x3f4);
            U(0x3cc) = U(0x3ac);
            U(0x3c8) = U(0x3f8);
            U(0x3d0) = U(0x3b0);
            U(0x3d4) = U(0x3b4);
            U(0x3dc) = U(0x3fc);
            U(0x3d8) = U(0x3b8);
            U(0x3e0) = U(0x400);
            U(0x3e4) = U(0x404);
            U(0x3ec) = U(0x40c);
            U(0x3e8) = U(0x408);
            U(0x3f0) = U(0x410);
            U(0x3f4) = U(0x414);
            U(0x3f8) = U(0x418);
            U(0x3ac) = U(0x41c);
            U(0x3b0) = U(0x420);
            U(0x3b4) = U(0x424);
            U(0x3fc) = U(0x42c);
            U(0x3b8) = U(0x428);
            U(0x400) = U(0x430);
            U(0x404) = U(0x434);
            U(0x408) = U(0x438);
            this[0x44c] = 1;
            this[0x44d] = 1;
            this[0x44b] = 1;
        }
        U(0x445) = 0x1010101;
        U(0x449) = 0x1010101;
        this[0x44d] = 1;
        I(0x54) = i - 1;
        I(0x6c) = i - 1;
        I(0x58) = j - 1;
        I(0x5c) = i;
        I(0x60) = j - 1;
        I(0x64) = i + 1;
        I(0x68) = j - 1;
        I(0x70) = j;
        I(0x4c) = i;
        I(0x50) = j;
        I(0x7c) = i - 1;
        I(0x74) = i + 1;
        I(0x78) = j;
        I(0x80) = j + 1;
        I(0x84) = i;
        I(0x88) = j + 1;
        I(0x8c) = i + 1;
        I(0x90) = j + 1;
        this[0x2dd] = 1;
    }
    if (!this[0x44e]) {
        int w = I(0x2e4), h = I(0x2e8);
        pos[0] = (float)((long double)(I(0x4c + p * 8) * w) + F(0x30c) + (long double)(w / 2));
        pos[2] = (float)(-((long double)(I(0x50 + p * 8) * h) - F(0x308)) - (long double)(h / 2));
    }
    {
        float m[16];
        sub_005B803E(m, pos[0], 0.0f, pos[2]);
        __builtin_memcpy(this + 0x94 + p * 0x40, m, 0x40);
        sub_005B809E(C(0x364 + p * 4), 0xc, C(0x340 + p * 4), 0x10, m, U(0x320));
    }
    if (this[0x2dd] && this[0x445 + p]) {
        int *cnt = (int *)(this + 0x3ac + p * 0x10), n;
        cnt[0] = 0;
        cnt[2] = 0;
        cnt[3] = 0;
        cnt[1] = 0;
        for (k = 0; k < I(0x320) / 4; k++)
            plant_5B6370(this, p, k, &cnt[0]);
        imp_qsort(C(0x340 + p * 4), I(0x320) / 4, 0x10, d_005B4EE0);
        for (k = I(0x320) / 4; k < I(0x320) / 2; k++)
            plant_5B6370(this, p, k, &cnt[1]);
        n = I(0x320) / 4;
        imp_qsort(C(0x340 + p * 4) + n * 0x10, n, 0x10, d_005B4EE0);
        for (k = I(0x320) / 2; k < I(0x320) / 4 * 3; k++)
            plant_5B6370(this, p, k, &cnt[2]);
        imp_qsort(C(0x340 + p * 4) + I(0x320) / 2 * 0x10, I(0x320) / 4, 0x10, d_005B4EE0);
        for (k = I(0x320) / 4 * 3; k < I(0x320); k++)
            plant_5B6370(this, p, k, &cnt[3]);
        imp_qsort(C(0x340 + p * 4) + I(0x320) * 3 / 4 * 0x10, I(0x320) / 4, 0x10, d_005B4EE0);
    }
    for (k = 0; k < I(0x318); k++) {
        float *t = (float *)(this + 0xc4 + k * 0x40), z = t[2], r = (float)(I(0x2e4) / 2);
        float y = sub_00473110(C(0x2c), t[0], z);
        this[0x43c + k] = sub_00457F80(C(0x48), 0, t[0], y, z, r) != 0;
    }
    {
        float t = F(0x334);
        int a = (int)(long long)(D(d_00609E08) * t), b = (int)(long long)(t / D(d_0060ACC0)),
            cc = (int)(long long)(t * D(d_00607CE0));
        int *cnt = (int *)(this + 0x3ac + p * 0x10);
        for (k = 0; k < cnt[0]; k++)
            fade_5B6370(this, p, k, cam, a, b, cc);
        for (k = I(0x320) / 4; k < I(0x320) / 4 + cnt[1]; k++)
            fade_5B6370(this, p, k, cam, a, b, cc);
        for (k = I(0x320) / 2; k < I(0x320) / 2 + cnt[2]; k++)
            fade_5B6370(this, p, k, cam, a, b, cc);
        for (k = I(0x320) * 3 / 4; k < I(0x320) * 3 / 4 + cnt[3]; k++)
            fade_5B6370(this, p, k, cam, a, b, cc);
    }
    return 0;
}
