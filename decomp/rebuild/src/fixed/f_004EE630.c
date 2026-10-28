/* 0x004EE630: a unit's sound group (this) follows the unit at the time (arg 1): the unit's clock (vf80 * vf88) going
 * back resets the schedule (0x004EE310 on +0x28 from +0x10); each idle sound (+0x14 vector, not vf24) moves to the
 * unit (vf68, 0x004C2E10 relative by vf20) at the volume of arg 1 (vf18); unless muted (+0x38), a pending sound
 * (+0x2C) that is not playing yet (vf20) starts (vf0C(1), past +0x39 from the offset into it) once the clock is
 * within its slot (+0x04, 24 bytes each: +0x10 the start, its length vf30, +0x14 started) and is marked started;
 * with none pending the group is retired (0x004EE240, whose EAX input only feeds its unused result); +0x39 cleared */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004EE310(void *self, void *src);
DECOMP_C unsigned int __cdecl sub_004EE240(void *g, void *eax, int a);
DECOMP_C void __thiscall sub_004C2E10(void *self, void *pos, int a);
typedef double (__thiscall *vft_4EE630)(void *self);
typedef void *(__thiscall *vf_4EE630)(void *self);
typedef char (__thiscall *vfb_4EE630)(void *self);
typedef unsigned int (__thiscall *vfu_4EE630)(void *self);
typedef void (__thiscall *vol_4EE630)(void *self, float v, int a);
typedef void (__thiscall *play_4EE630)(void *self, int a, int at);

DECOMP(004EE630)
void __thiscall f_004EE630(void *this, float t, void *unit)
{
    char *s = (char *)this;
    double a = ((vft_4EE630)(*(void ***)unit)[0x88 / 4])(unit);
    float now = (float)(((vft_4EE630)(*(void ***)unit)[0x80 / 4])(unit) * a);
    char idle = 1, rel;
    unsigned int i, len;
    void **snd;
    char *e;
    void **v;
    if (*(float *)(s + 0x3c) > now)
        sub_004EE310(s + 0x28, s + 0x10);
    *(float *)(s + 0x3c) = now;
    for (i = 0;; i++) {
        v = *(void ***)(s + 0x14);
        if (!v || i >= (unsigned int)((char *)*(void ***)(s + 0x18) - (char *)v) >> 2)
            break;
        snd = (void **)v[i];
        if (!snd || ((vfb_4EE630)(*(void ***)snd)[0x24 / 4])(snd))
            continue;
        rel = ((vfb_4EE630)(*(void ***)snd)[0x20 / 4])(snd);
        sub_004C2E10(snd, ((vf_4EE630)(*(void ***)unit)[0x68 / 4])(unit), rel);
        ((vol_4EE630)(*(void ***)snd)[0x18 / 4])(snd, t, 0);
        if (s[0x38] || !(*(void ***)(s + 0x2c))[i])
            continue;
        idle = 0;
        if (((vfb_4EE630)(*(void ***)snd)[0x20 / 4])(snd))
            continue;
        e = *(char **)(s + 4) + i * 0x18;
        if (!(now >= *(float *)(e + 0x10)))
            continue;
        len = ((vfu_4EE630)(*(void ***)snd)[0x30 / 4])(snd);
        if (!((double)len + *(float *)(e + 0x10) > now))
            continue;
        e = *(char **)(s + 4) + i * 0x18;
        if (e[0x14])
            continue;
        if (!s[0x39])
            ((play_4EE630)(*(void ***)snd)[0xc / 4])(snd, 1, 0);
        else
            ((play_4EE630)(*(void ***)snd)[0xc / 4])(snd, 1, (int)(long long)(now - *(float *)(e + 0x10)));
        (*(char **)(s + 4))[i * 0x18 + 0x14] = 1;
        (*(void ***)(s + 0x2c))[i] = 0;
    }
    if (idle)
        sub_004EE240(this, (void *)(size_t)(v ? i : 0), 0);
    s[0x39] = 0;
}
