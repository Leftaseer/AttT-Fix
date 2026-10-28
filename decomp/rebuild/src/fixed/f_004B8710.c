/* 0x004B8710: draws the selection marker over obj: at its position (vf68) raised by twice its height (vf7C) plus the
 * double at 0x607CE0 (D3DXMatrixTranslation, times the marker's own matrix +0x60), its quad (vertex buffer +0x5C,
 * texture +0x44 vf28) drawn as a two-triangle strip for each pass of its effect (+0x3C); returns what End returned */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C float *__stdcall sub_005B803E(float *out, float x, float y, float z);        /* D3DXMatrixTranslation */
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);     /* D3DXMatrixMultiply */
DECOMP_C char d_006C8C10[], d_00607CE0[];
typedef float *(__thiscall *vf68_4B8710)(void *self);
typedef float (__thiscall *vf7C_4B8710)(void *self);
typedef unsigned int (__thiscall *Begin_4B8710)(void *fx, unsigned int *passes, unsigned int flags);
typedef unsigned int (__thiscall *vf1_4B8710)(void *self, unsigned int a);
typedef unsigned int (__thiscall *vf_4B8710)(void *self);
typedef long (__stdcall *SetTransform_4B8710)(void *dev, unsigned int state, const void *m);
typedef long (__stdcall *SetSS_4B8710)(void *dev, unsigned int n, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *SetTexture_4B8710)(void *dev, unsigned int stage, void *tex);
typedef long (__stdcall *Draw_4B8710)(void *dev, unsigned int type, unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(004B8710)
unsigned int __thiscall f_004B8710(void *this, void *obj)
{
    char *s = (char *)this;
    float *p = ((vf68_4B8710)VT(obj)[0x68 / 4])(obj);
    float pos[3], m1[16], m2[16], h;
    unsigned int passes, i;
    void **fx, **dev, **t;
    SetTexture_4B8710 st;
    pos[1] = p[1];
    pos[0] = p[0];
    pos[2] = p[2];
    h = ((vf7C_4B8710)VT(obj)[0x7c / 4])(obj);
    fx = *(void ***)(s + 0x3c);
    pos[1] = (float)((h + h) + *(double *)d_00607CE0 + pos[1]);
    ((Begin_4B8710)VT(fx)[0x18 / 4])(fx, &passes, 0);
    sub_005B803E(m1, pos[0], pos[1], pos[2]);
    sub_005B8020(m2, s + 0x60, m1);
    __builtin_memcpy(m1, m2, 0x40);
    ((SetTransform_4B8710)VT(DEV)[0xb0 / 4])(DEV, 0x100, m1);
    ((SetSS_4B8710)VT(DEV)[0x190 / 4])(DEV, 0, *(void **)(s + 0x5c), 0, 0x14);
    dev = DEV;
    st = (SetTexture_4B8710)VT(dev)[0x104 / 4];
    t = *(void ***)(s + 0x44);
    st(DEV, 0, (void *)((vf_4B8710)VT(t)[0x28 / 4])(t));
    for (i = 0; i < passes; i++) {
        fx = *(void ***)(s + 0x3c);
        ((vf1_4B8710)VT(fx)[0x20 / 4])(fx, i);
        ((Draw_4B8710)VT(DEV)[0x144 / 4])(DEV, 5, 0, 2);
        fx = *(void ***)(s + 0x3c);
        ((vf_4B8710)VT(fx)[0x24 / 4])(fx);
    }
    fx = *(void ***)(s + 0x3c);
    return ((vf_4B8710)VT(fx)[0x1c / 4])(fx);
}
