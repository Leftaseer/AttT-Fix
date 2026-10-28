/* 0x005332D0: CNpc::vf37 (render): when asked to draw (a) and shown (+0x324): vf2D(a), the transform (+0x1C0) kept
 * at +0x328, the animation (+0x1A8: 0x0058FC30); while it is under the time at 0x615808 (0x0058EB70) and visible
 * (0x0058EB50, given 0 for the EAX the original leaves there) the model (+0x260) gets vf28(+0x2E4) and, near the
 * camera (0x00463E20 of the position: the matrix's x and z, y 0; vfEC of the model; +0x98: under 11), vfC0(11);
 * then vf2E, whose result is returned (a itself when not drawn) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0058FC30(void *self);
DECOMP_C float __thiscall sub_0058EB70(void *self);
DECOMP_C unsigned int __cdecl sub_0058EB50(void *self, unsigned int eax);
DECOMP_C int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
DECOMP_C char d_00615808[], d_006C8C10[], d_006CA0A4[];
typedef unsigned int (__thiscall *vf_005332D0)(void *self);
typedef unsigned int (__thiscall *vf1_005332D0)(void *self, unsigned int a);
typedef long (__stdcall *SetTransform_005332D0)(void *dev, unsigned int state, const void *m);

DECOMP(005332D0)
unsigned int __thiscall f_005332D0(void *this, unsigned int a, unsigned int b)
{
    char *s = (char *)this;
    void **m;
    float pos[3];
    int lvl;
    if (!(char)a || !s[0x324])
        return a;
    ((vf1_005332D0)(*(void ***)this)[0xb4 / 4])(this, a);
    __builtin_memcpy(s + 0x328, *(void **)(s + 0x1c0), 0x40);
    sub_0058FC30(*(void **)(s + 0x1a8));
    if (*(double *)d_00615808 > sub_0058EB70(*(void **)(s + 0x1a8)) && (char)sub_0058EB50(*(void **)(s + 0x1a8), 0)) {
        float *mx = *(float **)(s + 0x1c0);
        m = *(void ***)(s + 0x260);
        ((vf1_005332D0)(*(void ***)m)[0x28 / 4])(m, *(unsigned int *)(s + 0x2e4));
        ((unsigned int *)pos)[0] = ((unsigned int *)mx)[0x30 / 4];
        pos[1] = 0.0f;
        ((unsigned int *)pos)[2] = ((unsigned int *)mx)[0x38 / 4];
        m = *(void ***)(s + 0x260);
        lvl = sub_00463E20(pos, (void *)((vf_005332D0)(*(void ***)m)[0xec / 4])(m), s + 0x98);
        if (lvl < 0xb) {
            m = *(void ***)(s + 0x260);
            ((vf1_005332D0)(*(void ***)m)[0xc0 / 4])(m, 0xb);
        }
    }
    return ((vf_005332D0)(*(void ***)this)[0xb8 / 4])(this);
}
