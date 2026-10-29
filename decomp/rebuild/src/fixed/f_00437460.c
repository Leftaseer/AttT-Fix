/* 0x00437460: starts a camera flight (19 args): the start position (args 1-3, +0x70..) and target (4-6, +0x7C..),
 * the start (7-9, +0x88..) and end (10-12, +0x94..) angles, each end angle raised by 360 when it is over 180 below
 * the start (the shorter way round), the duration (13, +0x68); the camera (0x006CA2C4) is put at the start (+0x50..,
 * angles +0x5C.., +0x68 = 0, changed); the start direction (the start plus args 14-16) and the reversed end direction
 * (the target plus args 17-19) are normalised (D3DXVec3Normalize) and scaled by 0x006089A0 into +0xA0 / +0xAC; the
 * flight runs (+0x5D) from time 0 (+0x6C, +0x64). Returns what the original leaves in EAX (the last vector's y) */
/* @conv ECX 76 */
#include "auto_pre.h"
DECOMP_C float *__stdcall sub_005B8074(float *out, const float *v);                  /* D3DXVec3Normalize */
DECOMP_C char d_00609304[], d_00608974[], d_006CA2C4[], d_006089A0[], d_00608088[];

#define F(o) (*(float *)(s + (o)))
#define U(o) (*(unsigned int *)(s + (o)))

/* the shorter way round: 360 when the end is over 180 below the start, else 0 */
static float wrap_437460(float d)
{
    float t = __builtin_fabsf(d);
    return t > *(float *)d_00608974 && 0.0f > d ? *(float *)d_00609304 : 0.0f;
}

DECOMP(00437460)
unsigned int __thiscall f_00437460(void *this, float x, float y, float z, float tx, float ty, float tz, float ax,
                                   float ay, float az, float bx, float by, float bz, float dur, float ox, float oy,
                                   float oz, float px, float py, float pz)
{
    char *s = (char *)this, *cam;
    float dx, dy, dz, r, *v;
    F(0x70) = x, F(0x74) = y, F(0x78) = z;
    F(0x7c) = tx, F(0x80) = ty, F(0x84) = tz;
    F(0x88) = ax, F(0x8c) = ay, F(0x90) = az;
    F(0x94) = bx, F(0x98) = by, F(0x9c) = bz;
    dx = F(0x94) - F(0x88);
    dy = F(0x98) - F(0x8c);
    dz = F(0x9c) - F(0x90);
    r = wrap_437460(dx);
    F(0x94) = F(0x94) + r;
    r = wrap_437460(dy);
    F(0x98) = r + F(0x98);
    r = wrap_437460(dz);
    F(0x68) = dur;
    F(0x9c) = F(0x9c) + r;
    cam = *(char **)d_006CA2C4;
    *(float *)(cam + 0x50) = x;
    *(float *)(cam + 0x54) = y;
    *(float *)(cam + 0x58) = z;
    *(unsigned int *)(cam + 0x5c) = U(0x88);
    *(unsigned int *)(cam + 0x60) = U(0x8c);
    *(unsigned int *)(cam + 0x64) = U(0x90);
    *(float *)(cam + 0x68) = 0.0f;
    cam[0x70] = 1;
    v = (float *)(s + 0xa0);
    v[0] = x + ox;
    v[1] = oy + y;
    v[2] = oz + z;
    sub_005B8074(v, v);
    v[0] = (float)(v[0] * *(double *)d_006089A0);
    v[1] = (float)(v[1] * *(double *)d_006089A0);
    v[2] = (float)(*(double *)d_006089A0 * v[2]);
    v = (float *)(s + 0xac);
    v[0] = px + tx;
    v[1] = ty + py;
    v[2] = tz + pz;
    sub_005B8074(v, v);
    v[0] = (float)(v[0] * *(double *)d_006089A0);
    v[1] = (float)(v[1] * *(double *)d_006089A0);
    v[2] = (float)(*(double *)d_006089A0 * v[2]);
    v[0] = *(float *)d_00608088 - v[0];
    v[1] = *(float *)d_00608088 - v[1];
    v[2] = *(float *)d_00608088 - v[2];
    s[0x5d] = 1;
    F(0x6c) = 0.0f;
    *(int *)(s + 0x64) = 0;
    return *(unsigned int *)&v[1];
}
