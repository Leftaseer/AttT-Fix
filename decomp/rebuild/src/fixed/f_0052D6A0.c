/* 0x0052D6A0: a colour map's bilinear sample at (x, y) after the update 0x0052D3C0: the point is clamped to half
 * the map's size (+0, +4); 0x0052CC20 gives its cell, the quadrant (0..3) and the two signed fractions; the
 * quadrant's four neighbouring texels (clamped to +0x20 x +0x24) are read through the reader at +0x10 (on +8) as
 * ARGB / 255 and blended along x, then y, into out (red, green, blue), the alpha taken from 0x0068AE40 */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0052D3C0(void *self);
DECOMP_C void __thiscall sub_0052CC20(void *self, int *cell, float x, float y, int *quad, float *fy, float *fx);
DECOMP_C char d_00607CE0[], d_0060B368[], d_0068AE40[];
typedef unsigned int *(__thiscall *texel_52D6A0)(void *self, unsigned int *out, int x, int y);

static void texel_52D6A0_get(char *this, const int *p, float *c)
{
    unsigned int t, v = *((texel_52D6A0)*(void **)(this + 0x10))(this + 8, &t, p[0], p[1]);
    double k = *(double *)d_0060B368;
    c[0] = (float)((int)(v >> 16 & 0xff) * k);
    c[1] = (float)((int)(v >> 8 & 0xff) * k);
    c[2] = (float)((int)(v & 0xff) * k);
    c[3] = (float)((int)(v >> 24) * k);
}

/* r = a * (1 - w) + b * w, every product and sum a float */
static void mix_52D6A0(float *r, const float *a, const float *b, float w)
{
    float u = (float)(1.0f - w);
    int i;
    for (i = 0; i < 4; i++) {
        float pa = a[i] * u, pb = b[i] * w;
        r[i] = pa + pb;
    }
}

DECOMP(0052D6A0)
void __thiscall f_0052D6A0(void *self, float *out, float x, float y)
{
    char *this = (char *)self;
    double k, lim;
    int cell[2], quad, n[4][8], *e, w, h, i;
    float fx, fy, s[4][4], top[4], bot[4], r[4];

    sub_0052D3C0(this);
    k = *(double *)d_00607CE0;
    lim = *(float *)this * k;
    if (x > lim)
        x = (float)lim;
    lim = -*(float *)this * k;
    if (lim > x)
        x = (float)lim;
    lim = *(float *)(this + 4) * k;
    if (y > lim)
        y = (float)lim;
    lim = -*(float *)(this + 4) * k;
    if (lim > y)
        y = (float)lim;
    sub_0052CC20(this, cell, x, y, &quad, &fy, &fx);
    {
        int c0 = cell[0], c1 = cell[1];
        static const signed char d[4][8] = {
            { 0, -1, 1, -1, 1, 0, 0, 0 }, { 0, 0, 1, 0, 1, 1, 0, 1 },
            { -1, 0, 0, 0, 0, 1, -1, 1 }, { -1, -1, 0, -1, 0, 0, -1, 0 },
        };
        int q, j;
        for (q = 0; q < 4; q++)
            for (j = 0; j < 8; j += 2) {
                n[q][j] = c0 + d[q][j];
                n[q][j + 1] = c1 + d[q][j + 1];
            }
    }
    e = n[quad];
    w = *(int *)(this + 0x20);
    h = *(int *)(this + 0x24);
    for (i = 0; i < 8; i += 2) {
        if (e[i] < 0)
            e[i] = 0;
        if (e[i] >= w)
            e[i] = w - 1;
        if (e[i + 1] < 0)
            e[i + 1] = 0;
        if (e[i + 1] >= h)
            e[i + 1] = h - 1;
    }
    for (i = 0; i < 4; i++)
        texel_52D6A0_get(this, e + 2 * i, s[i]);
    {
        float ax = __builtin_fabsf(fx), ay = __builtin_fabsf(fy);
        if (fx > 0.0f) {
            mix_52D6A0(top, s[0], s[3], ax);
            mix_52D6A0(bot, s[1], s[2], ax);
        } else {
            mix_52D6A0(top, s[3], s[0], ax);
            mix_52D6A0(bot, s[2], s[1], ax);
        }
        if (fy > 0.0f)
            mix_52D6A0(r, top, bot, ay);
        else
            mix_52D6A0(r, bot, top, ay);
    }
    out[0] = r[0];
    out[1] = r[1];
    out[2] = r[2];
    out[3] = *(float *)d_0068AE40;
}
