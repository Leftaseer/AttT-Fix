/* 0x0043EAE0: world map visibility update (not while the world screen +0x40 of 0x006C88D8 is up): while the game
 * state (0x0042F160 +0x5C) differs from +0x70 or 0x006C892C +0x74 is set, a running camera path (0x004396C0,
 * 0x00436F30) is stopped (0x00436F00); otherwise with a viewer (+0x80) placed at the camera (0x00424E70 +0x44) the
 * 3x3 cells of 10 units (origin +0x40 / +0x3C, grid +0x4C, width +0x60, offset +0x5C) around it plus the extra cells
 * (+0xA4 / +0xA8, refreshed by 0x0043E8F0 when the hero +0x84 moved to another cell) go to the viewer (+0x44,
 * counting the filled ones at +0x1D4) and are shown (0x0043CCB0); the objects of +0xF0 and +0x100 within the
 * viewer's range (+0x414 * 10, plus each object's own +0x410) are collected (+0x3D8 / +0x3E4) and shown too. EAX is
 * left as the original leaves it */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__cdecl sub_004396C0(void);
DECOMP_C int __thiscall sub_00436F30(void *self);
DECOMP_C void __thiscall sub_00436F00(void *self);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void *__thiscall sub_0043F840(void *self);
DECOMP_C void __thiscall sub_0043BAD0(void *self, void *pos);
DECOMP_C void __thiscall sub_0043F430(void *self);
DECOMP_C unsigned char __thiscall sub_004ED050(void *self);
DECOMP_C void __thiscall sub_004BB120(void *self);
DECOMP_C void __thiscall sub_0043E8F0(void *self, int u, int v, int hu, int hv);
DECOMP_C int __thiscall sub_004CAC80(void *self);
DECOMP_C void __thiscall sub_004BA0B0(void *self);
DECOMP_C void __thiscall sub_0043CCB0(void *self, void *cells);
DECOMP_C int __thiscall sub_0043F710(void *self);
DECOMP_C float __thiscall sub_0043F6D0(void *self);
DECOMP_C float __thiscall sub_0043F6C0(void *self);
DECOMP_C void __thiscall sub_0043F470(void *self);
DECOMP_C char d_006C88D8[], d_006C892C[], d_0060A218[], d_006089A0[], d_0060A210[];
typedef float *(__thiscall *pos_43EAE0)(void *self);

#define CS (*(double *)d_006089A0)

static float *where_43EAE0(void *o)
{
    void *m = sub_0043F840(o);
    return ((pos_43EAE0)(*(void ***)m)[0x68 / 4])(m);
}

/* the grid cell (u, v) into the viewer's slot */
static void cell_43EAE0(char *this, char *view, void ***slot, int u, int v)
{
    char *c = *(char **)(this + 0x4c) + (*(int *)(this + 0x60) * u + *(int *)(this + 0x5c) + v) * 12;
    if (*(int *)(c + 4))
        (*(int *)(view + 0x1d4))++;
    *(*slot)++ = c;
}

/* objects of the vector at +off nearer than the range on both axes go to the list */
static void near_43EAE0(char *this, char *view, int off, int own, unsigned int *list, double cx, double cz)
{
    int cnt = *(char **)(this + off) ? (int)((*(char **)(this + off + 4) - *(char **)(this + off)) / 4) : 0, i;
    for (i = 0; i < cnt; i++) {
        void *o = (*(void ***)(this + off))[i];
        float p[3], r, d;
        if (!own && sub_0043F710(o) == 1)
            continue;
        __builtin_memcpy(p, where_43EAE0(o), 12);
        if (own)
            r = (float)((double)sub_0043F6C0((*(void ***)(this + off))[i]) + sub_0043F6D0(view) * CS);
        else
            r = (float)(sub_0043F6D0(view) * CS);
        d = (float)(cx - p[0]);
        d = __builtin_fabsf(d);
        if (!(r > d))
            continue;
        d = (float)(cz - p[2]);
        d = __builtin_fabsf(d);
        if (r > d && (int)list[2] < (int)list[1])
            ((void **)(size_t)list[0])[list[2]++] = (*(void ***)(this + off))[i];
    }
}

DECOMP(0043EAE0)
int __thiscall f_0043EAE0(char *this)
{
    char *g, *cam, *view;
    float c[3], *hp, h[3], dx, dz;
    int u, v, n, i;
    void **slot;
    double cx, cz;

    if (*(*(char **)d_006C88D8 + 0x40))
        return *(int *)d_006C88D8;
    g = sub_0042F160();
    if (*(int *)(g + 0x5c) != *(int *)(g + 0x70) || *(*(char **)d_006C892C + 0x74)) {
        void *path = sub_004396C0();
        int r = sub_00436F30(path);
        if ((char)r)
            sub_00436F00(path);
        return r;
    }
    if (!*(void **)(this + 0x80))
        return (int)(size_t)g;

    cam = sub_00424E70();
    view = *(char **)(this + 0x80);
    sub_0043BAD0(sub_0043F840(view), cam + 0x44);
    sub_0043F430(view);
    __builtin_memcpy(c, cam + 0x44, 12);
    {
        float ax = c[0], az = c[2];
        ax = __builtin_fabsf(ax);
        az = __builtin_fabsf(az);
        if (*(float *)d_0060A218 > ax || *(float *)d_0060A218 > az)
            return *(int *)&c[0];
    }
    cx = c[0];
    u = (int)((cx - *(float *)(this + 0x40)) / CS);
    cz = c[2];
    v = (int)((*(float *)(this + 0x3c) - cz) / CS);

    hp = where_43EAE0(*(void **)(this + 0x84));
    __builtin_memcpy(h, hp, 12);
    dx = (float)(h[0] - cx);
    dz = 0.0f - 0.0f;
    if ((long double)dx * dx + (long double)dz * dz > *(double *)d_0060A210)
        return *(int *)&h[2];

    if (!sub_004ED050(this + 0xec)) {
        int hu = (int)(((double)h[0] - *(float *)(this + 0x40)) / CS);
        int hv = (int)((*(float *)(this + 0x3c) - h[2]) / CS);
        sub_004BB120(this + 0xa4);
        sub_0043E8F0(this, u, v, hu, hv);
    }
    *(int *)(view + 0x1d4) = 0;
    slot = (void **)(view + 0x44);
    cell_43EAE0(this, view, &slot, u - 1, v - 1);
    cell_43EAE0(this, view, &slot, u, v - 1);
    cell_43EAE0(this, view, &slot, u + 1, v - 1);
    cell_43EAE0(this, view, &slot, u - 1, v);
    cell_43EAE0(this, view, &slot, u, v);
    cell_43EAE0(this, view, &slot, u + 1, v);
    cell_43EAE0(this, view, &slot, u - 1, v + 1);
    cell_43EAE0(this, view, &slot, u, v + 1);
    cell_43EAE0(this, view, &slot, u + 1, v + 1);
    n = sub_004CAC80(this + 0xa4);
    for (i = 0; i < n; i++) {
        int *e = *(int **)(this + 0xa8) + i * 2;
        cell_43EAE0(this, view, &slot, e[0], e[1]);
    }
    sub_004BA0B0(view + 0x14);
    view[0x10] = 0;
    if (*(int *)(view + 0x1d4) > 0)
        for (i = 0; i < n + 9; i++)
            if (((void **)(view + 0x44))[i])
                sub_0043CCB0(this, ((void **)(view + 0x44))[i]);

    *(int *)(view + 0x3e0) = 0;
    near_43EAE0(this, view, 0xf0, 0, (unsigned int *)(view + 0x3d8), cx, cz);
    *(int *)(view + 0x3ec) = 0;
    near_43EAE0(this, view, 0x100, 1, (unsigned int *)(view + 0x3e4), cx, cz);
    if (*(int *)(view + 0x3e0) > 0)
        sub_0043CCB0(this, view + 0x3d8);
    if (*(int *)(view + 0x3ec) > 0)
        sub_0043CCB0(this, view + 0x3e4);
    sub_0043F470(view);
    *(int *)(view + 0x3e0) = 0;
    *(int *)(view + 0x3ec) = 0;
    return 0;
}
