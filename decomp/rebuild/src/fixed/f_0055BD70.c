/* 0x0055BD70: lays out up to 5 objects by one of 37 random patterns (0x006C5550 + 120 * pattern: 5 kinds, then 5
 * records of 5 ints): object k takes the next entry (0x2C bytes, cycling the index of its kind) of the kind's list
 * (name at +4 + 0x2C*k, inner / outer radius at +0x1C / +0x20, ...); object 0 stays at the origin, every later one
 * is placed around the object its record names at a shuffled distance (inner .. outer sums, steps of 0.2) and angle
 * (steps of 0.0349 up to 2 pi; 0x00559A60 shuffles) until it is within the reach of that object and clear of the
 * others the record names (positions +0xE0 and +0x11C, 12 bytes each; +0x1BC counts the placements). Returns the
 * pattern */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
DECOMP_C void __stdcall sub_00559A60(float *a, int n);
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double), decomp_CIsqrt(double);
DECOMP_C char d_006C5550[], d_0061BFA8[], d_0061BFA0[], d_0061BF58[];

#define SHAPE(k) (this + 0x1c + (k) * 0x2c)                       /* +0 inner, +4 outer radius */
#define POS(k) ((float *)(this + 0xe0 + (k) * 0xc))
#define POS2(k) ((float *)(this + 0x11c + (k) * 0xc))
#define REC(k) ((int *)(this + 0x158 + (k) * 0x14))

static float sq_55BD70(float d)
{
    return (float)((long double)d * d);
}

/* distance in the ground plane of the point (x, z) from object k */
static float dist_55BD70(char *this, double x, double z, int k)
{
    float dx = (float)(x - POS(k)[0]), dz = (float)(z - POS(k)[2]);
    float a = sq_55BD70(dx), b = sq_55BD70(dz), s = (float)((long double)b + a);
    return (float)decomp_CIsqrt(s);
}

DECOMP(0055BD70)
int __thiscall f_0055BD70(char *this, char **lists, int *next, int *count)
{
    int r = imp_00607400() % 37, k;
    int *pat = (int *)(d_006C5550 + r * 120);
    float rad[4878], ang[362];

    *(int *)(this + 0x1bc) = 0;
    for (k = 0; k < 5; k++) {
        int kind = pat[k] - 1, j;
        char tmp[0x2c];
        *(int *)(SHAPE(k) - 4) = pat[k];
        __builtin_memcpy(REC(k), pat + 5 + k * 5, 20);
        if (kind < 0) {
            for (j = k; j < 5; j++) {
                this[4 + j * 0x2c] = 0;
                ((float *)SHAPE(j))[0] = 0.0f;
                ((float *)SHAPE(j))[1] = 0.0f;
                ((float *)SHAPE(j))[2] = 0.0f;
                ((float *)SHAPE(j))[3] = 0.0f;
            }
            break;
        }
        __builtin_memcpy(tmp, lists[kind] + next[kind] * 0x2c, 0x2c);
        if (++next[kind] >= count[kind])
            next[kind] = 0;
        __builtin_strcpy(this + 4 + k * 0x2c, tmp);
        __builtin_memcpy(SHAPE(k), tmp + 0x18, 0x14);
    }

    for (k = 0; k < 15; k++) {
        ((float *)(this + 0xe0))[k] = 0.0f;
        ((float *)(this + 0x11c))[k] = 0.0f;
    }
    (*(int *)(this + 0x1bc))++;
    for (k = 1; k < 5; k++) {
        int base, n1 = 0, n2 = 0, i1, i2;
        unsigned char ok;
        float v, lo, hi;
        if (pat[k] <= 0)
            return r;
        (*(int *)(this + 0x1bc))++;
        base = REC(k)[0];
        lo = (float)((long double)((float *)SHAPE(base))[0] + ((float *)SHAPE(k))[0]);
        hi = (float)((long double)((float *)SHAPE(base))[1] + ((float *)SHAPE(k))[1]);
        for (v = lo; hi >= v; v = (float)((long double)v + *(double *)d_0061BFA8))
            rad[n1++] = v;
        sub_00559A60(rad, n1);
        v = 0.0f;
        do {
            ang[n2++] = v;
            v = (float)((long double)v + *(double *)d_0061BFA0);
        } while (*(double *)d_0061BF58 > v);
        sub_00559A60(ang, n2);

        ok = 1;
        for (i1 = 0; i1 < n1 && ok; i1++)
            for (i2 = 0; i2 < n2 && ok; i2++) {
                double a = ang[i2], d = rad[i1];
                float x, z, dist;
                int nb, m;
                x = (float)((long double)(float)decomp_CIcos(a) * d + POS(REC(k)[0])[0]);
                POS(k)[1] = 0.0f;
                POS2(k)[1] = 0.0f;
                POS(k)[0] = x;
                POS2(k)[0] = x;
                z = (float)((long double)(float)decomp_CIsin(a) * d + POS(REC(k)[0])[2]);
                POS(k)[2] = z;
                POS2(k)[2] = z;
                nb = REC(k)[1];
                if (nb < 0) {
                    ok = 0;
                    break;
                }
                dist = dist_55BD70(this, x, z, nb);
                if (dist < (long double)((float *)SHAPE(nb))[0] + ((float *)SHAPE(k))[0])
                    continue;
                if ((long double)((float *)SHAPE(k))[1] + ((float *)SHAPE(nb))[1] < dist)
                    continue;
                ok = 0;
                for (m = 2; m < 5; m++) {
                    int o = REC(k)[m];
                    if (o < 0)
                        continue;
                    if ((long double)((float *)SHAPE(o))[1] + (double)((float *)SHAPE(k))[1] >
                        dist_55BD70(this, x, z, o)) {
                        ok = 1;
                        break;
                    }
                }
            }
    }
    return r;
}
