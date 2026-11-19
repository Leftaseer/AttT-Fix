/* 0x0053BA40: casts the cursor's view ray against the world map's ground mesh and returns the nearest hit.
 * The viewport object at +0x144 gives the scaled extents (vtable +0x8C / +0x90 over the screen size
 * 0x006C895C / 0x006C8958 and the projection's +0xC8 / +0xDC of the camera at +0x160) -> fx / fy; the camera's
 * view matrix (+0x88) is inverted (D3DXMatrixInverse 0x005B801A) and the ray becomes dir = row2 + fx*row0 +
 * fy*row1 with its origin at row3 (m[12..14]), while +0x44/+0x48/+0x4C hold the camera position again for the
 * hit distance.  The mesh at +0x98 has 0x20-byte vertices at +0x1EC and u16 index triples between +0x1FC and
 * +0x200 (6 bytes each, none when the list is null).  Each triangle is tested Moeller-Trumbore style: with
 * e1 = v1 - v0 and e2 = v2 - v0, n = dir x e2, den = n.e1 must be positive and at least 1e-4; then
 * u = n.(origin - v0)/den must lie in [0,1], v = dir.((origin - v0) x e1)/den must be non-negative and
 * u + v <= 1 (one reciprocal serves both divisions).  The hit v0 + u*e1 + v*e2 nearest to the camera position
 * by squared distance goes to the argument, and 1 is returned if any triangle was hit. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C void *__stdcall sub_005B801A(float *out, float *det, const float *m);        /* D3DXMatrixInverse */
DECOMP_C char d_0068AE00[], d_006C8958[], d_006C895C[];

typedef float (__thiscall *extent_53BA40)(void *self);

#define ONE_53BA40 (*(double *)d_0068AE00)
#define WIDTH_53BA40 (*(float *)d_006C895C)
#define HEIGHT_53BA40 (*(float *)d_006C8958)
#define EXTENT_53BA40(o, off) ((extent_53BA40)(*(void ***)(o))[(off) / 4])(o)

DECOMP(0053BA40)
unsigned char __thiscall f_0053BA40(void *this, float *out)
{
    char *c = (char *)this;
    char *cam = *(char **)(c + 0x160), *mesh = *(char **)(c + 0x98);
    void *vp = *(void **)(c + 0x144);
    float m[16];
    float fx = (float)(((EXTENT_53BA40(vp, 0x8c) * 2.0) / WIDTH_53BA40 - ONE_53BA40) /
                      *(float *)(cam + 0xc8));
    float fy = (float)-(((EXTENT_53BA40(vp, 0x90) * 2.0) / HEIGHT_53BA40 - ONE_53BA40) /
                        *(float *)(cam + 0xdc));
    float dirx, diry, dirz, eyex, eyey, eyez, camx, camy, camz;
    float *verts;
    unsigned short *ix;
    int tris, i;
    unsigned char hit = 0;
    float best = 0.0f;

    sub_005B801A(m, 0, (const float *)(cam + 0x88));
    dirx = fx * m[0] + fy * m[4] + m[8];
    diry = fx * m[1] + fy * m[5] + m[9];
    dirz = fy * m[6] + fx * m[2] + m[10];
    eyex = m[12];
    eyey = m[13];
    eyez = m[14];
    camx = *(float *)(cam + 0x44);
    camy = *(float *)(cam + 0x48);
    camz = *(float *)(cam + 0x4c);
    verts = *(float **)(mesh + 0x1ec);
    ix = *(unsigned short **)(mesh + 0x1fc);
    tris = ix ? (int)((*(char **)(mesh + 0x200) - (char *)ix) / 6) : 0;

    for (i = 0; i < tris; i++) {
        float *a = verts + ix[i * 3] * 8, *b = verts + ix[i * 3 + 1] * 8, *d = verts + ix[i * 3 + 2] * 8;
        float v0x = a[0], v0y = a[1], v0z = a[2];
        float v1x = b[0], v1y = b[1], v1z = b[2];
        float v2x = d[0], v2y = d[1], v2z = d[2];
        float e1x = v1x - v0x, e1y = v1y - v0y, e1z = v1z - v0z;
        float e2x = v2x - v0x, e2y = v2y - v0y, e2z = v2z - v0z;
        float nx = diry * e2z - dirz * e2y;
        float ny = dirz * e2x - dirx * e2z;
        float nz = dirx * e2y - diry * e2x;
        float den = (e1y * ny + e1x * nx) + e1z * nz;
        float tx, ty, tz, num, qx, qy, qz, dv, rec, u, v, hx, hy, hz, px, py, pz, dist;

        if (!(den > 0.0f))
            continue;
        tx = (float)((double)eyex - v0x);
        ty = (float)((double)eyey - v0y);
        tz = (float)((double)eyez - v0z);
        if (1e-4f > den)
            continue;
        num = (ny * ty + nx * tx) + nz * tz;
        if (0.0f > num)
            continue;
        if (num > den)
            continue;
        qx = ty * e1z - tz * e1y;
        qy = tz * e1x - tx * e1z;
        qz = tx * e1y - ty * e1x;
        dv = (dirx * qx + diry * qy) + dirz * qz;
        if (0.0f > dv)
            continue;
        if (num + dv > den)
            continue;
        rec = (float)(1.0 / den);
        u = num * rec;
        v = dv * rec;
        hx = (v0x + u * e1x) + v * e2x;
        hz = (v0z + u * e1z) + v * e2z;
        hy = (v0y + u * e1y) + v * e2y;
        px = hx - camx;
        py = hy - camy;
        pz = hz - camz;
        dist = (px * px + py * py) + pz * pz;
        if (!hit || dist < best) {
            best = dist;
            out[0] = hx;
            out[1] = hy;
            out[2] = hz;
            hit = 1;
        }
    }
    return hit;
}
