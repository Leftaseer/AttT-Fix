/* 0x0042E1E0: steps a projectile by t (the base update 0x004AD110 with EAX as it came) and returns what the step
 * produced.  Not flying (+0x2C0 clear): the trail (+0x2C8) decides (its +0x220 handler called on +0x228 with
 * +0x21C): if that returns nonzero, slot 1 of the trail's vtable advances it by t.  Flying: the time (+0x2B8) moves
 * on; past the arc's duration (+0x274/+0x270) only the rest of the step is walked (0x0042E030), the flight stops
 * (+0x2C0 = 0), the trail's +0x24C is cleared and its +0x24 rate is set from 0x0068AE10 / +0x2CC; otherwise the arc
 * point (0x0042D9E0) becomes +0x244 and 0x0042E030 carries the projectile on */
/* @conv EAX,ECX 4 */
/* @func 0042E1E0 custom */
#include "auto_pre.h"
typedef int (__thiscall *trail_check_42E1E0)(void *self, void *ctx);
typedef int (__thiscall *trail_step_42E1E0)(void *self, float t);
DECOMP_C unsigned int __cdecl sub_004AD110(void *self, unsigned int eax, float t);
DECOMP_C unsigned int __cdecl sub_0042E030(void *self, unsigned int eax, float t);
DECOMP_C float *__thiscall sub_0042D9E0(void *self, float *out, float t);
DECOMP_C char d_0068AE10[];                                            /* double */

DECOMP(0042E1E0)
unsigned int __cdecl f_0042E1E0(unsigned int in_eax, char *this, float t)
{
    char *s = (char *)this, *trail;
    unsigned int r = sub_004AD110(s, in_eax, t);
    float p[3], time, rest;
    if (!s[0x2c0]) {
        trail = *(char **)(s + 0x2c8);
        r = ((trail_check_42E1E0)(*(void **)(trail + 0x220)))(*(void **)(trail + 0x228), trail + 0x21c);
        if (r)
            r = ((trail_step_42E1E0)(*(void ***)trail)[1])(trail, t);
        return r;
    }
    time = *(float *)(s + 0x2b8) + t;
    if (*(float *)(s + 0x274) / *(float *)(s + 0x270) < time) {
        rest = *(float *)(s + 0x274) / *(float *)(s + 0x270) - *(float *)(s + 0x2b8);
        if (0.0f < rest)
            r = sub_0042E030(s, r, rest);
        s[0x2c0] = 0;
        trail = *(char **)(s + 0x2c8);
        trail[0x24c] = 0;
        *(float *)(trail + 0x24) = (float)(*(double *)d_0068AE10 / *(float *)(s + 0x2cc));
        return r;
    }
    sub_0042D9E0(s + 0x254, p, time);
    *(float *)(s + 0x244) = p[0];
    *(float *)(s + 0x248) = p[1];
    *(float *)(s + 0x24c) = p[2];
    r = sub_0042E030(s, (unsigned int)p, t);
    *(float *)(s + 0x2b8) = time;
    return r;
}
