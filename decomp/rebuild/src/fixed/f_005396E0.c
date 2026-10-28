/* 0x005396E0: CWorldHeroCreature::Tick (the EAX input passes on to the base tick, 0x004AC690): ticks the current
 * animation (+0x1E8, 0x004CB070) and the model (+0x1E4 vf14); while fading (+0x2C0) counts +0x2C4 down and sets the
 * model's effect (vf30) "dwTFactor" (vf44) to an alpha of 255 - count * step (+0x2C8, the top byte; -1 at the end);
 * updates (0x00538AE0) and, when the owner (+0x1CC) is in state 2 or has +0x1EB set, is not +0x4E4, this is not in
 * state 2 and 0x00538980 allows, switches to state 2 (the animation +0x1E0, started by 0x004CAFE0(0)) once near
 * enough to the owner's target (+0x498, 0x00538D80 below +0x200) and 0x00538C00 below the limit; then by state
 * (+0x1EC) 0: 0x00538FA0, 1: returns 0x005390D0, 2: 0x00539340, and moves by the model's step (0x0042AAB0 at the
 * speed +0x84, 0x004ACAC0, returned); another state returns it less 2 */
/* @conv ECX,EAX 0 */
/* @func 005396E0 custom */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_004AC690(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_004CB070(void *self);
DECOMP_C void __thiscall sub_00538AE0(void *self);
DECOMP_C char __thiscall sub_00538980(void *self);
DECOMP_C float __stdcall sub_00538D80(void *a, void *b, void *c);
DECOMP_C float __thiscall sub_00538C00(void *self);
DECOMP_C void __thiscall sub_004CAFE0(void *self, char a);
DECOMP_C void __thiscall sub_00538FA0(void *self);
DECOMP_C int __thiscall sub_005390D0(void *self);
DECOMP_C void __thiscall sub_00539340(void *self);
DECOMP_C void *__thiscall sub_0042AAB0(void *self, void *out, float speed);
DECOMP_C int __thiscall sub_004ACAC0(void *self, void *step);
DECOMP_C char d_0060A708[], d_00609620[], d_00615C38[];
typedef void *(__thiscall *vf_5396E0)(void *self);
typedef void (__thiscall *set_5396E0)(void *self, const char *name, int v);

DECOMP(005396E0)
int __cdecl f_005396E0(void *this, unsigned int eax)
{
    char *s = (char *)this;
    unsigned int pos[3], out[3];
    void **m, **o;
    int v, st;
    float d;
    sub_004AC690(this, eax);
    sub_004CB070(*(void **)(s + 0x1e8));
    m = *(void ***)(s + 0x1e4);
    ((vf_5396E0)(*(void ***)m)[0x14 / 4])(m);
    if (s[0x2c0]) {
        if (--*(int *)(s + 0x2c4) == 0) {
            s[0x2c0] = 0;
            m = *(void ***)(s + 0x1e4);
            m = (void **)((vf_5396E0)(*(void ***)m)[0x30 / 4])(m);
            v = -1;
        } else {
            v = (unsigned char)(int)(*(double *)d_00609620 -
                                     (double)*(unsigned int *)(s + 0x2c4) * *(float *)(s + 0x2c8)) << 24;
            m = *(void ***)(s + 0x1e4);
            m = (void **)((vf_5396E0)(*(void ***)m)[0x30 / 4])(m);
        }
        ((set_5396E0)(*(void ***)m)[0x44 / 4])(m, d_0060A708, v);
    }
    sub_00538AE0(this);
    o = *(void ***)(s + 0x1cc);
    if ((*(int *)((char *)o + 0x1e4) == 2 || ((char *)o)[0x1eb]) && !((char *)o)[0x4e4] &&
        *(int *)(s + 0x1ec) != 2 && sub_00538980(this)) {
        o = *(void ***)(s + 0x1cc);
        pos[0] = ((unsigned int *)o)[0x498 / 4];
        pos[1] = ((unsigned int *)o)[0x49c / 4];
        pos[2] = ((unsigned int *)o)[0x4a0 / 4];
        d = sub_00538D80(s + 0x64, ((vf_5396E0)(*(void ***)o)[0x68 / 4])(o), pos);
        if (*(float *)(s + 0x200) > d && (d = sub_00538C00(this), *(double *)d_00615C38 > d)) {
            *(int *)(s + 0x1ec) = 2;
            *(void **)(s + 0x1e8) = *(void **)(s + 0x1e0);
            sub_004CAFE0(*(void **)(s + 0x1e0), 0);
        }
    }
    st = *(int *)(s + 0x1ec);
    if (st == 0)
        sub_00538FA0(this);
    else if (st == 1)
        return sub_005390D0(this);
    else if (st == 2)
        sub_00539340(this);
    else
        return st - 2;
    return sub_004ACAC0(this, sub_0042AAB0(*(void **)(s + 0x1e4), out, *(float *)(s + 0x84)));
}
