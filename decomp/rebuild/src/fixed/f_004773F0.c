/* 0x004773F0: CTweenAnim::Blend(frame, subset): both clamped (frame to the count at +0x28, subset to +0x38), the mesh
 * (+0x2C) prepares them (vf08), then each material of the subset (12-byte entries at +0x34: the 0x6C-byte materials
 * at +4, their count at +8) is set unless the mesh does it (vf0C: else SetMaterial), its texture (+0x60, vf28) set,
 * and its triangles drawn (DrawIndexedPrimitive(D3DPT_TRIANGLELIST, 0, 0, vertices +0x24 of the mesh, start +0x64 as
 * a word, count +0x68)); the mesh finishes the frame (vf10) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_006C8C10[];
typedef void (__thiscall *vf2_4773F0)(void *self, unsigned int a, unsigned int b);
typedef char (__thiscall *vf0C_4773F0)(void *self, void *mat, unsigned int frame);
typedef void (__thiscall *vf1_4773F0)(void *self, unsigned int a);
typedef void *(__thiscall *vf_4773F0)(void *self);
typedef long (__stdcall *SetMaterial_4773F0)(void *dev, const void *m);
typedef long (__stdcall *SetTexture_4773F0)(void *dev, unsigned int stage, void *tex);
typedef long (__stdcall *DrawIndexed_4773F0)(void *dev, unsigned int type, int base, unsigned int min,
                                              unsigned int n, unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(004773F0)
void __thiscall f_004773F0(void *this, unsigned int frame, unsigned int subset)
{
    char *s = (char *)this;
    unsigned int n = *(unsigned int *)(s + 0x28), i, off;
    void **mesh;
    unsigned int *e;
    if (!n)
        frame = 0;
    else if (frame >= n)
        frame = n - 1;
    if (subset >= *(unsigned int *)(s + 0x38))
        subset = *(unsigned int *)(s + 0x38) - 1;
    mesh = *(void ***)(s + 0x2c);
    ((vf2_4773F0)VT(mesh)[2])(mesh, frame, subset);
    e = (unsigned int *)(*(char **)(s + 0x34) + subset * 0xc);
    for (i = 0, off = 0; i < e[2]; i++, off += 0x6c) {
        char *g = (char *)e[1] + off;
        mesh = *(void ***)(s + 0x2c);
        if (!((vf0C_4773F0)VT(mesh)[3])(mesh, g, frame))
            ((SetMaterial_4773F0)VT(DEV)[0xc4 / 4])(DEV, g);
        if (*(void **)(g + 0x60)) {
            void **dev = DEV, **t = *(void ***)(g + 0x60);
            SetTexture_4773F0 st = (SetTexture_4773F0)VT(dev)[0x104 / 4];
            st(DEV, 0, ((vf_4773F0)VT(t)[0x28 / 4])(t));
        }
        ((DrawIndexed_4773F0)VT(DEV)[0x148 / 4])(DEV, 4, 0, 0, (*(unsigned int **)(s + 0x2c))[9],
                                                 *(unsigned short *)(g + 0x64), *(unsigned int *)(g + 0x68));
        e = (unsigned int *)(*(char **)(s + 0x34) + subset * 0xc);
    }
    mesh = *(void ***)(s + 0x2c);
    ((vf1_4773F0)VT(mesh)[4])(mesh, frame);
}
