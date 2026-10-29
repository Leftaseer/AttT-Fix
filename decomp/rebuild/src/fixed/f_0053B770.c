/* 0x0053B770: the camera zoom by keys of the world view, the same code as 0x00459C30 with its own fields (key states
 * +0x88, keys +0x168 out / +0x169 in, camera +0x160, speed +0x190, acceleration +0x184, direction +0x1A0 / +0x198,
 * limits +0x1A8..+0x1AC when +0x1B0; dt +0x40), accelerating by 0x0053A7C0 (its EAX input only passed through) and
 * braking by 0x0053A820 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_0053A7C0(void *self, unsigned int eax, float *v);
DECOMP_C void __thiscall sub_0053A820(void *self, float *v);
DECOMP_C char d_0068AE40[], d_006092E8[], d_00607CE0[], d_00608B50[];

#define F(o) (*(float *)(s + (o)))

/* the braking distance at the current speed, as the original rounds it */
static float brake_53B770(char *s)
{
    float x = F(0x190), a = F(0x184), t = (float)(-x / a);
    return (float)((a * t) * t * *(double *)d_00607CE0 + x * t);
}

DECOMP(0053B770)
void __thiscall f_0053B770(void *this)
{
    char *s = (char *)this, *kb = *(char **)(s + 0x88), *cam;
    float *v = (float *)(s + 0x190), x, step, d;
    int out = kb[0x48 + (unsigned char)s[0x168]] & 0x80, in = kb[0x48 + (unsigned char)s[0x169]] & 0x80;
    if (out ? !in : in) {
        unsigned int dir = out ? *(unsigned int *)d_0068AE40 : *(unsigned int *)d_006092E8;
        if (!s[0x1b0]) {
            *(unsigned int *)(s + 0x198) = dir;
            sub_0053A7C0(this, 0, v);
        } else {
            *(unsigned int *)(s + 0x1a0) = dir;
            d = brake_53B770(s);
            cam = *(char **)(s + 0x160);
            if (!(d * *(double *)d_00608B50 >= (out ? F(0x1ac) - *(float *)(cam + 0x68)
                                                    : *(float *)(cam + 0x68) - F(0x1a8))))
                sub_0053A7C0(this, 0, v);
            else
                sub_0053A820(this, v);
        }
    } else {
        x = *v;
        if (x != 0.0f) {
            x = (float)(F(0x184) * F(0x40) + x);
            *v = x;
            if (0.0f > x)
                *v = 0.0f;
        }
    }
    step = (float)(F(0x1a0) * *v * F(0x40));
    cam = *(char **)(s + 0x160);
    cam[0x70] = 1;
    *(float *)(cam + 0x68) = step + *(float *)(cam + 0x68);
    if (s[0x1b0]) {
        float dist = *(float *)(cam + 0x68), lo = F(0x1a8), hi;
        if (!(lo < dist)) {
            *(float *)(cam + 0x68) = lo;
            cam[0x70] = 1;
            *v = 0.0f;
            return;
        }
        hi = F(0x1ac);
        if (!(dist < hi)) {
            *(float *)(cam + 0x68) = hi;
            cam[0x70] = 1;
            *v = 0.0f;
        }
    }
}
