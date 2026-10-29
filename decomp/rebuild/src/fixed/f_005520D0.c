/* 0x005520D0: NParticleSystem::CParticleSystem::BuildQuads: the emitter matrix (0x004ACDC0 when the world is shown and
 * the +0x59C mode is not 1, else 0x004ACD60) times the camera matrix (+0x88) moves every particle (+0x0C to +0x84);
 * with the +0x420 flag the list (+0x5C4) is sorted (0x00551CE0); then the shared vertex buffer (0x6CAAF8) is locked
 * for 4 vertices of 0x18 bytes per particle: colour ARGB from the floats +0x3C,+0x30,+0x34,+0x38 times 255 (clamped),
 * atlas cell from the frame word +0x70 by the column word +0x4C0 (1/count from the +0x4C0 provider), half size +0x7C;
 * with +0x410 the corners (0x6C5148) are rotated by +0x80 (RotationZ, scaled, translated), else axis-aligned */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C float *__thiscall sub_004ACD60(void *self, float *out);
DECOMP_C float *__thiscall sub_004ACDC0(void *self, float *out);
DECOMP_C void __thiscall sub_00551CE0(void *self, int pred);
DECOMP_C void **__thiscall sub_004BA550(void *self);
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);      /* D3DXMatrixMultiply */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);     /* D3DXVec3TransformCoord */
DECOMP_C float *__stdcall sub_005B8038(float *out, float a);                           /* D3DXMatrixRotationZ */
DECOMP_C float *__stdcall sub_005B809E(void *out, unsigned ostride, const void *v, unsigned vstride,
                                      const void *m, unsigned n);                     /* D3DXVec3TransformCoordArray */
DECOMP_C char d_006C88D8[];
DECOMP_C char d_006C5148[];
DECOMP_C char d_006CAAF8[];
typedef int (__thiscall *getter_5520D0)(void *obj, void *arg);
typedef unsigned short (__thiscall *getw_5520D0)(void *obj, void *arg);
typedef char (__thiscall *getb_5520D0)(void *obj, void *arg);
typedef long (__stdcall *lock_5520D0)(void *vb, unsigned off, unsigned size, char **p, unsigned flags);
typedef long (__stdcall *unlock_5520D0)(void *vb);

static int clamp_5520D0(int v)
{
    return v < 0 ? 0 : v > 0xff ? 0xff : v;
}

DECOMP(005520D0)
void __thiscall f_005520D0(char *this)
{
    char *cam = sub_00424E70();
    char *prov = *(char **)(this + 0x59c);
    float buf[16], mat[16], *m, rot[16];
    char **head, **node, *p = 0, *vt;
    void *vb;
    float inv;
    unsigned base;

    if (*(*(char **)d_006C88D8 + 0x40) &&
        ((getter_5520D0)*(void **)(prov + 0xc))(*(void **)(prov + 0x14), prov + 8) != 1)
        m = sub_004ACDC0(this, buf);
    else
        m = sub_004ACD60(this, buf);
    sub_005B8020(mat, m, cam + 0x88);

    head = *(char ***)(this + 0x5c8);
    for (node = (char **)*head; node != head; node = (char **)*node)
        sub_005B8026((float *)((char *)node + 0x84), (float *)((char *)node + 0xc), mat);

    if (((getb_5520D0)*(void **)(this + 0x424))(*(void **)(this + 0x42c), this + 0x420))
        sub_00551CE0(this + 0x5c4, 0);

    vb = *sub_004BA550(d_006CAAF8);
    ((lock_5520D0)(*(void ***)vb)[0x2c / 4])(vb, 0, *(unsigned *)(this + 0x5cc) * 0x60, &p, 0);
    if (!p)
        return;

    head = *(char ***)(this + 0x5c8);
    inv = 1.0f / (float)((getw_5520D0)*(void **)(this + 0x4c4))(*(void **)(this + 0x4cc), this + 0x4c0);
    base = 0;
    for (node = (char **)*head; node != head; node = (char **)*node, base += 0x60) {
        char *n = (char *)node;
        int r = (int)(*(float *)(n + 0x30) * 255.0);
        int g = (int)(*(float *)(n + 0x34) * 255.0);
        int b = (int)(*(float *)(n + 0x38) * 255.0);
        int a = (int)(255.0 * *(float *)(n + 0x3c));
        unsigned col = ((unsigned)clamp_5520D0(a) << 24) | (clamp_5520D0(r) << 16) | (clamp_5520D0(g) << 8) |
                       clamp_5520D0(b);
        float h = (float)(*(float *)(n + 0x7c) * 0.5);
        int cols = *(unsigned short *)(this + 0x4c0), fr = *(unsigned short *)(n + 0x70);
        float cq = (float)(fr / cols), cr = (float)(fr % cols);
        float px = *(float *)(n + 0x84), py = *(float *)(n + 0x88), pz = *(float *)(n + 0x8c);
        float u0, u1, v0, v1;
        float *vx = (float *)(p + base);

        if (*(this + 0x410)) {
            int i;
            sub_005B8038(rot, *(float *)(n + 0x80));
            for (i = 0; i < 3; i++) {
                rot[i * 4 + 0] *= h;
                rot[i * 4 + 1] *= h;
                rot[i * 4 + 2] *= h;
            }
            rot[12] = px;
            rot[13] = py;
            rot[14] = pz;
            sub_005B809E(vx, 0x18, d_006C5148, 0xc, rot, 4);
        } else {
            float x0 = px + -h, y0 = py + -h, y1 = py + h, x1 = px + h;
            vx[0] = x0;  vx[1] = y0;  vx[2] = pz;
            vx[6] = x0;  vx[7] = y1;  vx[8] = pz;
            vx[12] = x1; vx[13] = y1; vx[14] = pz;
            vx[18] = x1; vx[19] = y0; vx[20] = pz;
        }
        u0 = cr * inv;
        u1 = (cr + 1.0f) * inv;
        v0 = cq * inv;
        v1 = (cq + 1.0f) * inv;
        vt = (char *)vx;
        *(unsigned *)(vt + 0x0c) = col;
        *(unsigned *)(vt + 0x24) = col;
        *(unsigned *)(vt + 0x3c) = col;
        *(unsigned *)(vt + 0x54) = col;
        vx[4] = u0;  vx[5] = v1;
        vx[10] = u0; vx[11] = v0;
        vx[16] = u1; vx[17] = v0;
        vx[22] = u1; vx[23] = v1;
    }
    ((unlock_5520D0)(*(void ***)vb)[0x30 / 4])(vb);
}
