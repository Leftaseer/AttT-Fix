/* 0x0045C060: a gizmo's draw (arg 1: the full pass, arg 2 passed on): begins (vfB4), updates the animation
 * (+0x1A8: 0x0058FC30) and, unless the full pass is past its time (+0x264 not above 0x0058EB70), when it plays
 * (0x0058EB50, its EAX input only passed through, approximated): a plain pass draws the overlay (+0x258 vf94(0, arg
 * 2)); a full pass draws the overlay once past +0x260, else the body (+0x254 vf94(arg 1, 0)), first giving its
 * effect (vf30) the two texture scrolls ("mStage0TCMove": scale +0x2E4/+0x2E8, offset +0x2DC/+0x2E0 times +0x2D8 /
 * 1000; "mStage1TCMove": +0x2F4/+0x2F8, +0x2EC/+0x2F0) when scrolling (+0x2D4). Ends (vfB8) and returns its result */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0058FC30(void *self);
DECOMP_C float __thiscall sub_0058EB70(void *self);
DECOMP_C unsigned int __cdecl sub_0058EB50(void *self, unsigned int eax);
DECOMP_C char d_0068AE10[], d_0060B930[], d_0060B920[];
typedef int (__thiscall *vf_45C060)(void *self);
typedef void (__thiscall *vfb_45C060)(void *self, unsigned char a);
typedef void (__thiscall *draw_45C060)(void *self, int a, int b);
typedef void *(__thiscall *fx_45C060)(void *self);
typedef void (__thiscall *mat_45C060)(void *self, const char *name, void *m);

#define U(o) (*(unsigned int *)(s + (o)))
#define F(o) (*(float *)(s + (o)))

DECOMP(0045C060)
int __thiscall f_0045C060(void *this, unsigned char full, int arg)
{
    char *s = (char *)this;
    void **o;
    float k;
    ((vfb_45C060)(*(void ***)this)[0xb4 / 4])(this, full);
    sub_0058FC30(*(void **)(s + 0x1a8));
    if ((!full || F(0x264) > sub_0058EB70(*(void **)(s + 0x1a8))) &&
        (char)sub_0058EB50(*(void **)(s + 0x1a8), 0)) {
        if (!full) {
            o = *(void ***)(s + 0x258);
            if (o)
                ((draw_45C060)(*(void ***)o)[0x94 / 4])(o, 0, arg);
        } else if (*(void **)(s + 0x258) && sub_0058EB70(*(void **)(s + 0x1a8)) > F(0x260)) {
            o = *(void ***)(s + 0x258);
            ((draw_45C060)(*(void ***)o)[0x94 / 4])(o, full, arg);
        } else {
            if (s[0x2d4]) {
                unsigned int m1[16] = { 0 }, m2[16] = { 0 };
                k = (float)(F(0x2d8) / *(double *)d_0068AE10);
                m1[0] = U(0x2e4);
                m1[5] = U(0x2e8);
                m2[0] = U(0x2f4);
                m2[5] = U(0x2f8);
                ((float *)m1)[8] = F(0x2dc) * k;
                ((float *)m1)[9] = F(0x2e0) * k;
                ((float *)m2)[8] = F(0x2ec) * k;
                ((float *)m2)[9] = k * F(0x2f0);
                o = *(void ***)(s + 0x254);
                o = (void **)((fx_45C060)(*(void ***)o)[0x30 / 4])(o);
                ((mat_45C060)(*(void ***)o)[0x50 / 4])(o, d_0060B930, m1);
                o = *(void ***)(s + 0x254);
                o = (void **)((fx_45C060)(*(void ***)o)[0x30 / 4])(o);
                ((mat_45C060)(*(void ***)o)[0x50 / 4])(o, d_0060B920, m2);
            }
            o = *(void ***)(s + 0x254);
            ((draw_45C060)(*(void ***)o)[0x94 / 4])(o, full, 0);
        }
    }
    return ((vf_45C060)(*(void ***)this)[0xb8 / 4])(this);
}
