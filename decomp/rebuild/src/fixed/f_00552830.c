/* 0x00552830: a particle system's draw (arg 1 passed to begin, arg 2 unused): begins (vfB4), updates the animation
 * (+0x1A8: 0x0058FC30) and, when it plays (0x0058EB50, its EAX input only passed through), is not hidden (vf60) and
 * its origin (provider +0x2E4 plus the position +0x64/+0x6C) is within +0x600 (squared, horizontally) of the camera
 * (0x006CA2C4), draws its +0x5CC particles: fills the shared quad buffer (0x005520D0, 0x006CAAF8: 0x004BA550 /
 * 0x004BA4D0) and draws it as indexed triangles (indices 0x006CAAF0, FVF +0x5BC, no shader) on the device +0x5F4
 * with the world and view set to identity (0x006C5108; the view saved from 0x00424E70's +0x88, 0x00435640, and put
 * back), per pass of the effect +0x3C with the texture of +0x44. Ends (vfB8) and returns its result */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0058FC30(void *self);
DECOMP_C unsigned int __cdecl sub_0058EB50(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_005520D0(void *self);
DECOMP_C void **__thiscall sub_004BA550(void *self);
DECOMP_C int __thiscall sub_004BA4D0(void *self);
DECOMP_C char *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_00435640(void *self);
DECOMP_C char d_006CA2C4[], d_006CAAF8[], d_006CAAF0[], d_006C5108[];
typedef int (__thiscall *vf_552830)(void *self);
typedef void (__thiscall *vfa_552830)(void *self, int a);
typedef char (__thiscall *vfb_552830)(void *self);
typedef unsigned int *(__thiscall *vec_552830)(void *obj, void *out, void *self);
typedef void *(__thiscall *vfp_552830)(void *self);
typedef void (__thiscall *begin_552830)(void *self, unsigned int *passes, int flags);
typedef long (__stdcall *dev1_552830)(void *dev, void *a);
typedef long (__stdcall *dev2_552830)(void *dev, unsigned int a, void *b);
typedef long (__stdcall *src_552830)(void *dev, unsigned int stream, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *draw_552830)(void *dev, unsigned int type, int base, unsigned int min, unsigned int n,
                                      unsigned int start, unsigned int count);

#define F(o) (*(float *)(s + (o)))

DECOMP(00552830)
int __thiscall f_00552830(void *this, int a1, int a2)
{
    char *s = (char *)this, *cam, *p = s + 0x2e4;
    void **dev, **fx, **t;
    unsigned int tmp[3], *v, m[16], passes, i, n;
    float x, z, px, pz, dx, dz, d2;
    ((vfa_552830)(*(void ***)this)[0xb4 / 4])(this, a1);
    sub_0058FC30(*(void **)(s + 0x1a8));
    if (!(char)sub_0058EB50(*(void **)(s + 0x1a8), 0))
        goto end;
    if (((vfb_552830)(*(void ***)this)[0x60 / 4])(this))
        goto end;
    v = ((vec_552830)((void **)p)[3])(((void **)p)[5], tmp, p);
    ((unsigned int *)&x)[0] = v[0];
    ((unsigned int *)&z)[0] = v[2];
    px = x + F(0x64);
    pz = F(0x6c) + z;
    cam = *(char **)d_006CA2C4;
    dx = *(float *)(cam + 0x44) - px;
    dz = *(float *)(cam + 0x4c) - pz;
    d2 = (float)(dx * dx + 0.0 * 0.0 + dz * dz);
    if (d2 >= F(0x600) || !*(int *)(s + 0x5cc))
        goto end;
    sub_005520D0(this);
    dev = *(void ***)(s + 0x5f4);
    ((src_552830)(*(void ***)dev)[0x190 / 4])(dev, 0, *sub_004BA550(d_006CAAF8), 0, 0x18);
    dev = *(void ***)(s + 0x5f4);
    ((dev1_552830)(*(void ***)dev)[0x1a0 / 4])(dev, *(void **)d_006CAAF0);
    dev = *(void ***)(s + 0x5f4);
    ((dev1_552830)(*(void ***)dev)[0x170 / 4])(dev, 0);
    dev = *(void ***)(s + 0x5f4);
    ((dev1_552830)(*(void ***)dev)[0x164 / 4])(dev, *(void **)(s + 0x5bc));
    __builtin_memcpy(m, sub_00424E70() + 0x88, 64);
    sub_00435640(sub_00424E70());
    dev = *(void ***)(s + 0x5f4);
    ((dev2_552830)(*(void ***)dev)[0xb0 / 4])(dev, 0x100, d_006C5108);
    dev = *(void ***)(s + 0x5f4);
    ((dev2_552830)(*(void ***)dev)[0xb0 / 4])(dev, 2, d_006C5108);
    fx = *(void ***)(s + 0x3c);
    if (fx) {
        ((begin_552830)(*(void ***)fx)[0x18 / 4])(fx, &passes, 0);
        for (i = 0; i < passes; i++) {
            fx = *(void ***)(s + 0x3c);
            ((vfa_552830)(*(void ***)fx)[0x20 / 4])(fx, i);
            dev = *(void ***)(s + 0x5f4);
            t = *(void ***)(s + 0x44);
            ((dev2_552830)(*(void ***)dev)[0x104 / 4])(dev, 0, ((vfp_552830)(*(void ***)t)[0x28 / 4])(t));
            n = *(unsigned int *)(s + 0x5cc);
            dev = *(void ***)(s + 0x5f4);
            ((draw_552830)(*(void ***)dev)[0x148 / 4])(dev, 4, 0, 0, n * 4, 0, n * 2);
            fx = *(void ***)(s + 0x3c);
            ((vf_552830)(*(void ***)fx)[0x24 / 4])(fx);
        }
        fx = *(void ***)(s + 0x3c);
        ((vf_552830)(*(void ***)fx)[0x1c / 4])(fx);
    }
    dev = *(void ***)(s + 0x5f4);
    ((dev2_552830)(*(void ***)dev)[0xb0 / 4])(dev, 2, m);
    sub_004BA4D0(d_006CAAF8);
end:
    return ((vf_552830)(*(void ***)this)[0xb8 / 4])(this);
}
