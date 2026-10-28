/* 0x0042DEE0: launches a projectile (the Fury's spear) at the target: the current transform (+0x1D4) kept at +0x214,
 * the start (+0x244, through the owner's (+0x2BC) matrix +0x168: D3DXVec3TransformCoord), the flight (0x0042DC20 of
 * +0x254: from the start to the target's position (vf68) raised by its height (0x00511CD0) times the double at
 * 0x608B50, with the floats at 0x608B48 / 0x608B4C), the clocks (+0x2B8, +0x2D4, +0x2D8) reset, the trail's particle
 * system (+0x2C8: its emitter delegate at +0x2E4 given the start, its rate the double at 0x68AE10 / +0x2D0, then
 * 0x0054FE30(0, 0)) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int x, y, z; } V3_42DEE0;           /* (copied as dwords) */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C float __thiscall sub_00511CD0(void *self);
DECOMP_C void __thiscall sub_0042DC20(void *self, V3_42DEE0 a, V3_42DEE0 b, float c, float d);
DECOMP_C void __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C char d_00608B50[], d_00608B48[], d_00608B4C[], d_0068AE10[];
typedef unsigned int *(__thiscall *vf68_42DEE0)(void *self);
typedef void (__thiscall *emit_42DEE0)(void *ctx, void *d, void *pos);

DECOMP(0042DEE0)
void __thiscall f_0042DEE0(void *this, void *target)
{
    char *s = (char *)this;
    char *owner = *(char **)(s + 0x2bc), *ps, *e;
    V3_42DEE0 v, t;
    unsigned int *p;
    float y;
    __builtin_memcpy(s + 0x214, s + 0x1d4, 0x40);
    v.x = *(unsigned int *)(s + 0x244);
    v.y = *(unsigned int *)(s + 0x248);
    v.z = *(unsigned int *)(s + 0x24c);
    s[0x2c0] = 1;
    sub_005B8026((float *)&v, (float *)&v, owner + 0x168);
    p = ((vf68_42DEE0)(*(void ***)target)[0x68 / 4])(target);
    t.x = p[0];
    y = ((float *)p)[1];
    t.z = p[2];
    y = (float)(sub_00511CD0(target) * *(double *)d_00608B50 + y);
    t.y = *(unsigned int *)&y;
    sub_0042DC20(s + 0x254, v, t, *(float *)d_00608B48, *(float *)d_00608B4C);
    *(float *)(s + 0x2b8) = 0.0f;
    *(float *)(s + 0x2d4) = 0.0f;
    e = *(char **)(s + 0x2c8) + 0x2e4;
    (*(emit_42DEE0 *)(e + 0x10))(*(void **)(e + 0x14), e, &v);
    ps = *(char **)(s + 0x2c8);
    *(float *)(ps + 0x24) = (float)(*(double *)d_0068AE10 / *(float *)(s + 0x2d0));
    sub_0054FE30(*(void **)(s + 0x2c8), 0, 0.0f);
    *(float *)(s + 0x2d8) = 0.0f;
}
