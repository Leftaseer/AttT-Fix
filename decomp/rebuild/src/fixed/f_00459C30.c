/* 0x00459C30: the camera zoom by keys (this +0x7C's key states at +0x48: zoom out +0x105, zoom in +0x104): one key
 * held sets the direction (+1 / -1; into +0x138 when limited by +0x144, else +0x130) and, when limited, accelerates
 * (0x004597B0, its EAX input only passed through) while the braking distance (speed * t + acceleration * t * t / 2,
 * t = -speed / acceleration (+0x11C), times 1.5) is short of the limit (+0x140 out / +0x13C in) and brakes
 * (0x00459810) after; neither (or both) decays the speed (+0x120) by the acceleration times dt (+0x40) to 0. The
 * camera distance (+0x100's +0x68, changed +0x70) moves by direction * speed * dt, clamped to +0x13C..+0x140 (the
 * speed stopping there) when limited */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004597B0(void *self, unsigned int eax, float *v);
DECOMP_C void __thiscall sub_00459810(void *self, float *v);
DECOMP_C char d_0068AE40[], d_006092E8[], d_00607CE0[], d_00608B50[];

#define F(o) (*(float *)(s + (o)))

/* the braking distance at the current speed, as the original rounds it */
static float brake_459C30(char *s)
{
    float x = F(0x120), a = F(0x11c), t = (float)(-x / a);
    return (float)((a * t) * t * *(double *)d_00607CE0 + x * t);
}

DECOMP(00459C30)
void __thiscall f_00459C30(void *this)
{
    char *s = (char *)this, *kb = *(char **)(s + 0x7c), *cam;
    float *v = (float *)(s + 0x120), x, step, d;
    int out = kb[0x48 + (unsigned char)s[0x105]] & 0x80, in = kb[0x48 + (unsigned char)s[0x104]] & 0x80;
    if (out ? !in : in) {
        unsigned int dir = out ? *(unsigned int *)d_0068AE40 : *(unsigned int *)d_006092E8;
        if (!s[0x144]) {
            *(unsigned int *)(s + 0x130) = dir;
            sub_004597B0(this, 0, v);
        } else {
            *(unsigned int *)(s + 0x138) = dir;
            d = brake_459C30(s);
            cam = *(char **)(s + 0x100);
            if (!(d * *(double *)d_00608B50 >= (out ? F(0x140) - *(float *)(cam + 0x68)
                                                    : *(float *)(cam + 0x68) - F(0x13c))))
                sub_004597B0(this, 0, v);
            else
                sub_00459810(this, v);
        }
    } else {
        x = *v;
        if (x != 0.0f) {
            x = (float)(F(0x11c) * F(0x40) + x);
            *v = x;
            if (0.0f > x)
                *v = 0.0f;
        }
    }
    step = (float)(F(0x138) * *v * F(0x40));
    cam = *(char **)(s + 0x100);
    cam[0x70] = 1;
    *(float *)(cam + 0x68) = step + *(float *)(cam + 0x68);
    if (s[0x144]) {
        float dist = *(float *)(cam + 0x68), lo = F(0x13c), hi;
        if (!(lo < dist)) {
            *(float *)(cam + 0x68) = lo;
            cam[0x70] = 1;
            *v = 0.0f;
            return;
        }
        hi = F(0x140);
        if (!(dist < hi)) {
            *(float *)(cam + 0x68) = hi;
            cam[0x70] = 1;
            *v = 0.0f;
        }
    }
}
