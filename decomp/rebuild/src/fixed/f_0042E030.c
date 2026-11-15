/* 0x0042E030: walks the projectile's flight path in fixed time steps (1000 / +0x2D0) until the budget in +0x2D4
 * runs out.  The budget first grows by dt; every step samples the arc (1000 * step + +0x2B8 through +0x270/+0x274,
 * the same parabola as 0x0042D9E0) into a point, transforms it by +0x278 and hands it to the trail (+0x2C8:
 * its +0x2F4 handler on +0x2F8 with +0x2E4 and the point).  A puff is emitted through 0x00551F60: type 3 (and the
 * +0x2D8 counter restarting) once the counter passes 1000 / +0x2CC, type 1 otherwise; the counter then grows by
 * the step.  EAX goes in and out as it came (the last emission's result). */
/* @conv ECX,EAX 4 */
/* @func 0042E030 custom */
#include "auto_pre.h"
typedef void (__thiscall *trail_point_42E030)(void *self, void *ctx, float *pt);
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m); /* D3DXVec3TransformCoord */
DECOMP_C int __thiscall sub_00551F60(void *self, int type);
DECOMP_C char d_0068AE10[], d_00608B40[];                              /* double 1000.0, gravity */

DECOMP(0042E030)
unsigned int __cdecl f_0042E030(void *this, unsigned int eax, float dt)
{
    char *s = (char *)this;
    float step = (float)(*(double *)d_0068AE10 / *(float *)(s + 0x2d0));
    float counter = (float)(*(double *)d_0068AE10 / *(float *)(s + 0x2cc));
    float budget = dt + *(float *)(s + 0x2d4);
    int n = 1;
    *(float *)(s + 0x2d4) = budget;
    while (budget >= step) {
        char *trail = *(char **)(s + 0x2c8);
        float pt[3], t, x;
        t = step * (float)n + *(float *)(s + 0x2b8);
        x = t * *(float *)(s + 0x270) - *(float *)(s + 0x274) * 0.5f;
        pt[0] = x;
        pt[1] = (x * x / *(double *)d_00608B40) * *(float *)(s + 0x254);
        pt[2] = 0.0f;
        sub_005B8026(pt, pt, s + 0x278);
        ((trail_point_42E030)(*(void **)(trail + 0x2f4)))(*(void **)(trail + 0x2f8), trail + 0x2e4, pt);
        if (*(float *)(s + 0x2d8) < counter) {
            eax = sub_00551F60(trail, 1);
        } else {
            eax = sub_00551F60(trail, 3);
            *(float *)(s + 0x2d8) = 0.0f;
        }
        *(float *)(s + 0x2d8) += step;
        budget -= step;
        *(float *)(s + 0x2d4) = budget;
        n += 1;
    }
    return eax;
}
