/* 0x004DD860: the camera zoom by keys of another view, the same code as 0x00459C30 with its fields 0xF423C further
 * on (keys +0xF4341 / +0xF4340, camera +0xF433C, speed +0xF435C, acceleration +0xF4358, direction +0xF4374 / +0xF436C,
 * limits +0xF4378..+0xF437C when +0xF4380; dt +0x40 and the key states +0x7C as there), accelerating by 0x004DCF50
 * (its EAX input only passed through) and braking by 0x004DCFB0 */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004DCF50(void *self, unsigned int eax, float *v);
DECOMP_C void __thiscall sub_004DCFB0(void *self, float *v);
DECOMP_C char d_0068AE40[], d_006092E8[], d_00607CE0[], d_00608B50[];

#define F(o) (*(float *)(s + (o)))

/* the braking distance at the current speed, as the original rounds it */
static float brake_4DD860(char *s)
{
    float x = F(0xf435c), a = F(0xf4358), t = (float)(-x / a);
    return (float)((a * t) * t * *(double *)d_00607CE0 + x * t);
}

DECOMP(004DD860)
void __thiscall f_004DD860(void *this)
{
    char *s = (char *)this, *kb = *(char **)(s + 0x7c), *cam;
    float *v = (float *)(s + 0xf435c), x, step, d;
    int out = kb[0x48 + (unsigned char)s[0xf4341]] & 0x80, in = kb[0x48 + (unsigned char)s[0xf4340]] & 0x80;
    if (out ? !in : in) {
        unsigned int dir = out ? *(unsigned int *)d_0068AE40 : *(unsigned int *)d_006092E8;
        if (!s[0xf4380]) {
            *(unsigned int *)(s + 0xf436c) = dir;
            sub_004DCF50(this, 0, v);
        } else {
            *(unsigned int *)(s + 0xf4374) = dir;
            d = brake_4DD860(s);
            cam = *(char **)(s + 0xf433c);
            if (!(d * *(double *)d_00608B50 >= (out ? F(0xf437c) - *(float *)(cam + 0x68)
                                                    : *(float *)(cam + 0x68) - F(0xf4378))))
                sub_004DCF50(this, 0, v);
            else
                sub_004DCFB0(this, v);
        }
    } else {
        x = *v;
        if (x != 0.0f) {
            x = (float)(F(0xf4358) * F(0x40) + x);
            *v = x;
            if (0.0f > x)
                *v = 0.0f;
        }
    }
    step = (float)(F(0xf4374) * *v * F(0x40));
    cam = *(char **)(s + 0xf433c);
    cam[0x70] = 1;
    *(float *)(cam + 0x68) = step + *(float *)(cam + 0x68);
    if (s[0xf4380]) {
        float dist = *(float *)(cam + 0x68), lo = F(0xf4378), hi;
        if (!(lo < dist)) {
            *(float *)(cam + 0x68) = lo;
            cam[0x70] = 1;
            *v = 0.0f;
            return;
        }
        hi = F(0xf437c);
        if (!(dist < hi)) {
            *(float *)(cam + 0x68) = hi;
            cam[0x70] = 1;
            *v = 0.0f;
        }
    }
}
