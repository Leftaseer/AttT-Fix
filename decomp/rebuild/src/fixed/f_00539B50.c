/* 0x00539B50: CWorldHeroCreature::Render: when shown (+0x218): 0x004AC890 and, within the distance at 0x615808 of
 * the camera (0x6CA2C4 +0x44: the squared distance as a float), the level of detail (0x00463E20 of the position +0x64,
 * the camera's vfEC and +0x98) for the model (+0x1E4 vfC0); then its flag (+0x27C), if any, is placed at the matrix
 * +0x280 times +0x168 with its height on the terrain (0x00473110), set as the world transform and drawn (vf08) */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 00539B50 custom */
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);   /* D3DXMatrixMultiply */
DECOMP_C char d_006CA2C4[], d_006CA2D0[], d_006C8C10[], d_00615808[];
typedef void *(__thiscall *vfEC_539B50)(void *self);
typedef unsigned int (__thiscall *vf1_539B50)(void *self, unsigned int a);
typedef unsigned int (__thiscall *vf_539B50)(void *self);
typedef long (__stdcall *SetTransform_539B50)(void *dev, unsigned int state, const void *m);

DECOMP(00539B50)
unsigned int __cdecl f_00539B50(void *this, unsigned int eax)
{
    char *s = (char *)this;
    if (s[0x218]) {
        float *cam, *p = (float *)(s + 0x64), dx, dy, dz, d2;
        sub_004AC890(this);
        cam = (float *)(*(char **)d_006CA2C4 + 0x44);
        eax = (unsigned int)(cam - 0x11);
        dx = cam[0] - p[0];
        dy = cam[1] - p[1];
        dz = cam[2] - p[2];
        d2 = dx * dx + dy * dy + dz * dz;
        if (*(double *)d_00615808 > d2) {
            void **c = **(void ****)(*(char **)(s + 0x1e0) + 0x14);
            void **r = *(void ***)(s + 0x1e4);
            vf1_539B50 lod = (vf1_539B50)(*(void ***)r)[0xc0 / 4];
            int lvl = sub_00463E20(p, ((vfEC_539B50)(*(void ***)c)[0xec / 4])(c), s + 0x98);
            eax = lod(*(void **)(s + 0x1e4), lvl);
        }
    }
    if (*(void **)(s + 0x27c)) {
        float m[16];
        void **dev, **o;
        sub_005B8020(m, s + 0x280, s + 0x168);
        m[13] = sub_00473110(*(void **)d_006CA2D0, m[12], m[14]);
        dev = *(void ***)d_006C8C10;
        ((SetTransform_539B50)(*(void ***)dev)[0xb0 / 4])(dev, 0x100, m);
        o = *(void ***)(s + 0x27c);
        eax = ((vf_539B50)(*(void ***)o)[2])(o);
    }
    return eax;
}
