/* 0x005204B0: NTrajectoryMove's text along a path (points, count, font): the font (+0x6C) fills the static string
 * 0x006CA9A8 (CSimpleStack<unsigned int>, created once) for the path's length and gives the letter scale; the
 * frames (+0x0C / +0x10, 0x14 each: letter, x, y, angle in degrees, scale) are then laid out. Two points: the letters
 * advance (0x0042AD00) along the line, sin / cos of its heading at +0x70 / +0x74. More points: the letters advance
 * along the current segment, and when the walked length reaches the segment's end the next segment's heading is
 * given to the last five frames (from four before the letter, as the original does even before the first frame);
 * on the last segment the scale is fitted so that the rest of the letters end at the last point. Then each frame is
 * moved across the path by the letter's height (0x0042AC50). Fewer points: the points (relative to the first) are
 * fitted by parabolas through each three (0x00520020, +0x64 / +0x68), after making x run one way (swapping x and y,
 * or mirroring x); the original stores stack garbage as these frames' scale, the scale is used here */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_005E3F71(void *fn);                       /* atexit */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);             /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                        /* operator delete[] */
DECOMP_C double __thiscall sub_0042AD00(void *font, unsigned int ch);
DECOMP_C double __thiscall sub_0042AC50(void *font, unsigned int ch);
DECOMP_C void __cdecl sub_004F6470(float *deg);
DECOMP_C float __thiscall sub_00520020(void *self, int c0, int c1, int c2);
DECOMP_C double decomp_CIsqrt(double), decomp_CIatan2(double y, double x), decomp_CIsin(double), decomp_CIcos(double);
DECOMP_C char d_006CA9A8[], d_006CA9B4[], d_00604DF0[], d_006095F0[], d_00609628[], d_006099D8[], d_00608528[],
    d_00614478[], d_00614474[], d_00608088[];
typedef void (__thiscall *vfe8_5204B0)(void *font, void *str, float len, float *scale);

#define D(a) (*(double *)(a))
#define FL(a) (*(float *)(a))
#define F(o) (*(float *)(this + (o)))
#define FONT (*(void **)(this + 0x6c))
#define CHARS (*(unsigned int **)(d_006CA9A8 + 4))
#define NCHARS (*(unsigned int *)(d_006CA9A8 + 8))
#define FRAMES (*(char **)(this + 0xc))
#define NFRAMES (*(unsigned int *)(this + 0x10))

/* new[] of n elements of size, saturating like the original */
static void *alloc_5204B0(unsigned int n, unsigned int size)
{
    unsigned long long s = (unsigned long long)n * size;
    return sub_005E3B10(s > 0xffffffffu ? 0xffffffffu : (unsigned int)s);
}

/* the heading of (dx, dy) in 0..2pi */
static float heading_5204B0(float dx, float dy)
{
    float a = (float)decomp_CIatan2(dx, dy);
    if (dx < 0)
        a = (float)(a + D(d_006095F0));
    return a;
}

/* the segment's heading in degrees (normalized by 0x004F6470) into *deg, its sin / cos at +0x70 / +0x74 */
static void dir_5204B0(char *this, float dx, float dy, float *deg)
{
    float t;
    *deg = (float)(heading_5204B0(dx, dy) * D(d_00609628) + D(d_006099D8));
    sub_004F6470(deg);
    t = (float)(*deg * D(d_00608528));
    F(0x70) = (float)decomp_CIsin(t);
    F(0x74) = (float)decomp_CIcos(t);
}

static void push_5204B0(char *this, unsigned int ch, float x, float y, float deg, float scale)
{
    char *f = FRAMES + NFRAMES * 0x14;
    *(unsigned int *)f = ch;
    *(float *)(f + 4) = x;
    *(float *)(f + 8) = y;
    *(float *)(f + 0xc) = deg;
    *(float *)(f + 0x10) = scale;
    NFRAMES++;
}

/* each frame moved across the path by its letter's height */
static void across_5204B0(char *this)
{
    unsigned int i;
    for (i = 0; i < NFRAMES; i++) {
        char *f = FRAMES + i * 0x14;
        float sc = *(float *)(f + 0x10), d, dx, dy;
        d = (float)(sub_0042AC50(FONT, *(unsigned int *)f) * sc);
        dx = d * F(0x74);
        dy = -d * F(0x70);
        *(float *)(f + 4) = dx + *(float *)(f + 4);
        *(float *)(f + 8) = dy + *(float *)(f + 8);
    }
}

static float len_5204B0(float dx, float dy)
{
    return (float)decomp_CIsqrt((float)(dx * dx + dy * dy));
}

/* the angle in degrees of the parabola's step (dx, dy) */
static float deg_5204B0(float dx, float dy)
{
    return (float)((heading_5204B0(dx, dy) + D(d_00614478)) * D(d_00609628));
}

DECOMP(005204B0)
void __thiscall f_005204B0(void *self, float *p, unsigned int n, void *font)
{
    char *this = (char *)self;
    float total = 0, scale, deg;
    unsigned int i;

    *(void **)(this + 0x6c) = font;
    if (!(*(unsigned int *)d_006CA9B4 & 1)) {
        *(unsigned int *)d_006CA9B4 |= 1;
        ((unsigned int *)d_006CA9A8)[0] = 0x613600;
        ((unsigned int *)d_006CA9A8)[1] = 0;
        ((unsigned int *)d_006CA9A8)[2] = 0;
        sub_005E3F71(d_00604DF0);
    }
    for (i = 0; i + 1 < n; i++)
        total = len_5204B0(p[2 * i + 2] - p[2 * i], p[2 * i + 3] - p[2 * i + 1]) + total;
    ((vfe8_5204B0)(*(void ***)font)[0xe8 / 4])(font, d_006CA9A8, total, &scale);
    NFRAMES = 0;
    if (n == 2) {
        float x, y;
        dir_5204B0(this, p[2] - p[0], p[3] - p[1], &deg);
        x = p[0];
        y = p[1];
        push_5204B0(this, CHARS[0], x, y, deg, scale);
        for (i = 1; i < NCHARS; i++) {
            unsigned int ch = CHARS[i];
            float adv = (float)(sub_0042AD00(FONT, ch) * scale);
            float dx = F(0x70) * adv, dy = adv * F(0x74);
            x = dx + x;
            y = y + dy;
            push_5204B0(this, ch, x, y, deg, scale);
        }
        across_5204B0(this);
        return;
    }
    if (n > 2) {
        float x, y, fscale = scale, acc = 0, end;
        unsigned int s = 1, j;
        unsigned int ch0 = CHARS[0];
        dir_5204B0(this, p[2] - p[0], p[3] - p[1], &deg);
        x = p[0];
        y = p[1];
        push_5204B0(this, ch0, x, y, deg, fscale);
        end = len_5204B0(p[2] - p[0], p[3] - p[1]);
        for (j = (unsigned int)-3; j + 4 < NCHARS; j++) {
            unsigned int ch = CHARS[j + 4];
            float adv = (float)(sub_0042AD00(FONT, ch) * scale);
            float dx = F(0x70) * adv, dy = adv * F(0x74);
            x = x + dx;
            y = y + dy;
            push_5204B0(this, ch, x, y, deg, fscale);
            if (s < n - 1) {
                double dend;
                acc = len_5204B0(dy, dx) + acc;
                dend = end;
                if (!(acc < end)) {
                    unsigned int k;
                    s++;
                    dir_5204B0(this, p[2 * s] - x, p[2 * s + 1] - y, &deg);
                    for (k = 0; k < 5; k++)
                        *(float *)(FRAMES + (j + k) * 0x14u + 0xc) = deg;
                    if (s == n - 1) {
                        float sx = 0, sy = 0, sum;
                        unsigned int m;
                        for (m = j + 5; m < NCHARS; m++) {
                            float d = (float)sub_0042AD00(FONT, CHARS[m]);
                            float ax = F(0x70) * d, ay = d * F(0x74);
                            sx = ax + sx;
                            sy = ay + sy;
                        }
                        sum = (float)(sx * sx + sy * sy);
                        end = len_5204B0(p[2 * s] - x, p[2 * s + 1] - y);
                        scale = (float)(end / (float)decomp_CIsqrt(sum));
                        fscale = scale;
                    } else {
                        end = (float)(len_5204B0(p[2 * s] - x, p[2 * s + 1] - y) + dend);
                    }
                }
            }
        }
        across_5204B0(this);
        return;
    }
    {
        float *t = (float *)alloc_5204B0(n, 8), *slots, *pv, *prev;
        unsigned char monotonic = 1, swapped = 0, mirrored = 0;
        unsigned int s, k, last = n - 1;
        float cx, cy, px, py, pdeg;

        for (i = 0; i < n; i++) {
            t[2 * i] = p[2 * i];
            t[2 * i + 1] = p[2 * i + 1];
            p[2 * i] = p[2 * i] - t[0];
            p[2 * i + 1] = p[2 * i + 1] - t[1];
        }
        /* x must run one way: otherwise x and y are swapped */
        if (p[0] > p[2]) {
            for (i = 1; i < n; i++)
                if (p[2 * i] >= p[2 * i - 2]) {
                    monotonic = 0;
                    break;
                }
        } else if (!(p[2] > p[0])) {
            monotonic = 0;
        } else {
            for (i = 1; i < n; i++)
                if (p[2 * i - 2] >= p[2 * i]) {
                    monotonic = 0;
                    break;
                }
        }
        if (monotonic) {
            if (!(p[2 * n - 1] > p[2 * n - 2]))
                goto sides;
            if (p[1] > p[3]) {
                for (i = 1; i < n; i++)
                    if (p[2 * i + 1] >= p[2 * i - 1])
                        goto sides;
            } else if (!(p[3] > p[1])) {
                goto sides;
            } else {
                for (i = 1; i < n; i++)
                    if (p[2 * i - 1] >= p[2 * i + 1])
                        goto sides;
            }
        }
        for (i = 0; i < n; i++) {
            float v = p[2 * i];
            p[2 * i] = p[2 * i + 1];
            p[2 * i + 1] = v;
        }
        swapped = 1;
    sides:
        if (p[0] > p[2 * n - 2]) {
            float c = FL(d_00608088);
            for (i = 1; i < n; i++)
                p[2 * i] = c - p[2 * i];
            mirrored = 1;
        }
        /* the letters walked along the polyline */
        slots = (float *)alloc_5204B0(NCHARS, 8);
        (void)(heading_5204B0(p[2] - p[0], p[3] - p[1]) + D(d_00614478));
        slots[0] = 0;
        slots[1] = 0;
        s = 1;
        pv = p + 2;
        prev = slots;
        for (i = 1; i < NCHARS; i++) {
            unsigned int ch = CHARS[i];
            double sc = scale;
            float h = (float)(sub_0042AC50(FONT, ch) * sc);
            float a = (float)(sub_0042AD00(FONT, ch) * sc);
            float sn = F(0x70), cs = F(0x74);
            float X = h * cs + a * sn, Y = a * cs - h * sn;
            float *cur = slots + 2 * i;
            cur[0] = (float)(X + prev[0]);
            cur[1] = (float)(prev[1] + Y);
            if (cur[0] > pv[0] && s != n - 1) {
                cur[0] = pv[0];
                cur[1] = pv[1];
                s++;
                pv = p + 2 * s;
                (void)(heading_5204B0(pv[0] - pv[-2], pv[1] - pv[-1]) + D(d_00614478));
            }
            prev = cur;
        }
        /* a parabola through each three points */
        if (*(void **)(this + 0x64)) {
            sub_005E3EBA(*(void **)(this + 0x64));
            *(void **)(this + 0x64) = 0;
        }
        if (last)
            *(void **)(this + 0x64) = alloc_5204B0(last, 0xc);
        *(int *)(this + 0x68) = 0;
        for (k = 0; k + 1 < last; k++) {
            float *q = p + 2 * k, *c, det;
            F(0x20) = q[0] * q[0];
            F(0x24) = q[0];
            F(0x30) = q[2] * q[2];
            F(0x34) = q[2];
            F(0x40) = q[4] * q[4];
            F(0x44) = q[4];
            F(0x2c) = q[1];
            F(0x3c) = q[3];
            F(0x4c) = q[5];
            (*(int *)(this + 0x68))++;
            c = *(float **)(this + 0x64) + 3 * k;
            det = sub_00520020(this, 0, 1, 2);
            c[0] = (float)(sub_00520020(this, 3, 1, 2) / (double)det);
            c[1] = (float)(sub_00520020(this, 0, 3, 2) / (double)det);
            c[2] = (float)(sub_00520020(this, 0, 1, 3) / (double)det);
        }
        (*(int *)(this + 0x68))++;
        {
            float *c = *(float **)(this + 0x64);
            int b = 3 * (int)n;
            c[b - 6] = c[b - 9];
            c[b - 5] = c[b - 8];
            c[b - 4] = c[b - 7];
        }
        /* the frames on the parabolas */
        pdeg = deg_5204B0(t[2] - t[0], t[3] - t[1]);
        push_5204B0(this, 0, t[0], t[1], pdeg, scale);
        cx = 0;
        cy = 0;
        px = 0;
        py = 0;
        k = 0;
        s = 1;
        for (i = 1; i < NCHARS; i++) {
            float *c, a;
            while (cx > p[2 * k + 2]) {
                if (k + 1 == last)
                    break;
                k++;
            }
            cx = slots[2 * i];
            if (cx > p[2 * s]) {
                do {
                    if (s == last)
                        break;
                    s++;
                    pdeg = deg_5204B0(t[2 * s] - t[2 * s - 2], t[2 * s + 1] - t[2 * s - 1]);
                } while (cx > p[2 * s]);
            }
            c = *(float **)(this + 0x64) + 3 * k;
            cy = (float)(c[0] * cx * cx + c[1] * cx + c[2]);
            if (mirrored)
                cx = FL(d_00608088) - cx;
            if (swapped) {
                float v = cx;
                cx = cy;
                cy = v;
            }
            a = deg_5204B0(cx - px, cy - py);
            if ((float)__builtin_fabsf((float)(a - pdeg)) > FL(d_00614474))
                a = *(float *)(FRAMES + NFRAMES * 0x14 - 8);
            push_5204B0(this, CHARS[i], (float)(t[0] + cx), (float)(t[1] + cy), a, scale);
            px = cx;
            py = cy;
        }
        sub_005E3EBA(slots);
        sub_005E3EBA(t);
    }
}
