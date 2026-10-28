/* 0x004CFB40: CSurfacePlane::Render: 0x00435640, the identity world transform (0x6C2540), its vertices (+0x70,
 * 20 bytes each) and indices (+0x74), and for each pass of its effect (+0x3C) its texture (+0x44 vf28) and
 * DrawIndexedPrimitive(D3DPT_TRIANGLELIST, 0, 0, +0x80 vertices, 0, +0x80 / 3 triangles); returns what the effect's
 * End returned */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00435640(void *self);
DECOMP_C char d_006CA2C4[], d_006C8C10[], d_006C2540[];
typedef long (__stdcall *SetTransform_4CFB40)(void *dev, unsigned int state, const void *m);
typedef long (__stdcall *SetSS_4CFB40)(void *dev, unsigned int n, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *SetPtr_4CFB40)(void *dev, void *p);
typedef long (__stdcall *SetTexture_4CFB40)(void *dev, unsigned int stage, void *tex);
typedef long (__stdcall *DrawIndexed_4CFB40)(void *dev, unsigned int type, int base, unsigned int min,
                                              unsigned int n, unsigned int start, unsigned int count);
typedef unsigned int (__thiscall *Begin_4CFB40)(void *fx, unsigned int *passes, unsigned int flags);
typedef unsigned int (__thiscall *vf1_4CFB40)(void *self, unsigned int a);
typedef unsigned int (__thiscall *vf_4CFB40)(void *self);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(004CFB40)
unsigned int __thiscall f_004CFB40(void *this)
{
    char *s = (char *)this;
    unsigned int passes = (unsigned int)this, i;
    void **fx;
    sub_00435640(*(void **)d_006CA2C4);
    ((SetTransform_4CFB40)VT(DEV)[0xb0 / 4])(DEV, 0x100, d_006C2540);
    ((SetSS_4CFB40)VT(DEV)[0x190 / 4])(DEV, 0, *(void **)(s + 0x70), 0, 0x14);
    ((SetPtr_4CFB40)VT(DEV)[0x1a0 / 4])(DEV, *(void **)(s + 0x74));
    fx = *(void ***)(s + 0x3c);
    ((Begin_4CFB40)VT(fx)[0x18 / 4])(fx, &passes, 0);
    for (i = 0; i < passes; i++) {
        void **dev, **t;
        unsigned int n;
        fx = *(void ***)(s + 0x3c);
        ((vf1_4CFB40)VT(fx)[0x20 / 4])(fx, i);
        dev = DEV;
        t = *(void ***)(s + 0x44);
        ((SetTexture_4CFB40)VT(dev)[0x104 / 4])(DEV, 0, (void *)((vf_4CFB40)VT(t)[0x28 / 4])(t));
        n = *(unsigned int *)(s + 0x80);
        ((DrawIndexed_4CFB40)VT(DEV)[0x148 / 4])(DEV, 4, 0, 0, n, 0, n / 3);
        fx = *(void ***)(s + 0x3c);
        ((vf_4CFB40)VT(fx)[0x24 / 4])(fx);
    }
    fx = *(void ***)(s + 0x3c);
    return ((vf_4CFB40)VT(fx)[0x1c / 4])(fx);
}
