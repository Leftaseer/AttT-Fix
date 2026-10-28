/* 0x005379C0: TownAnims::vf37 (render): vf2D(a), the animation (+0x1A8: 0x0058FC30); while it is under the time at
 * 0x615808 (0x0058EB70) and visible (0x0058EB50, given 0 for the EAX the original leaves there) its object at
 * +0x208 gets vf08, the world transform is the matrix +0x1C0 (also kept at 0x6CA0A4), and the model (+0x204) gets the
 * level of detail for the distance to the camera (0x00463E20 of the position: the matrix's x and z, y 0; vfEC of the
 * model; +0x98) by vfC0 when under 11; then vf2E, whose result is returned */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0058FC30(void *self);
DECOMP_C float __thiscall sub_0058EB70(void *self);
DECOMP_C unsigned int __cdecl sub_0058EB50(void *self, unsigned int eax);
DECOMP_C int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
DECOMP_C char d_00615808[], d_006C8C10[], d_006CA0A4[];
typedef unsigned int (__thiscall *vf_005379C0)(void *self);
typedef unsigned int (__thiscall *vf1_005379C0)(void *self, unsigned int a);
typedef long (__stdcall *SetTransform_005379C0)(void *dev, unsigned int state, const void *m);

DECOMP(005379C0)
unsigned int __thiscall f_005379C0(void *this, unsigned int a, unsigned int b)
{
    char *s = (char *)this;
    void **m;
    float pos[3];
    int lvl;
    ((vf1_005379C0)(*(void ***)this)[0xb4 / 4])(this, a);
    sub_0058FC30(*(void **)(s + 0x1a8));
    if (*(double *)d_00615808 > sub_0058EB70(*(void **)(s + 0x1a8)) && (char)sub_0058EB50(*(void **)(s + 0x1a8), 0)) {
        void **dev = *(void ***)d_006C8C10;
        float *mx;
        if (*(void **)(s + 0x208)) {
            m = *(void ***)(s + 0x208);
            ((vf_005379C0)(*(void ***)m)[2])(m);
        }
        dev = *(void ***)d_006C8C10;
        ((SetTransform_005379C0)(*(void ***)dev)[0xb0 / 4])(dev, 0x100, *(void **)(s + 0x1c0));
        *(void **)d_006CA0A4 = *(void **)(s + 0x1c0);
        mx = *(float **)(s + 0x1c0);
        ((unsigned int *)pos)[0] = ((unsigned int *)mx)[0x30 / 4];
        pos[1] = 0.0f;
        ((unsigned int *)pos)[2] = ((unsigned int *)mx)[0x38 / 4];
        m = *(void ***)(s + 0x204);
        lvl = sub_00463E20(pos, (void *)((vf_005379C0)(*(void ***)m)[0xec / 4])(m), s + 0x98);
        if (lvl < 0xb) {
            m = *(void ***)(s + 0x204);
            ((vf1_005379C0)(*(void ***)m)[0xc0 / 4])(m, lvl);
        }
    }
    return ((vf_005379C0)(*(void ***)this)[0xb8 / 4])(this);
}
