/* 0x004AE3E0: draws the meshes in the list at +0x2428 (when +0x242C, its size, is not 0): stage 0 gets the texture
 * of +0x2430 (vf28); each visible mesh (vf5C) sets the render states of +0x2434 by its flags (+0x248: 1 0x00435760,
 * 2 0x004357F0), its own texture at stage 1 (+0x244), D3DRS_TEXTUREFACTOR (+0x234), and per part (+0x208, 12 bytes
 * each, +0x20C of them) the index buffer 0x006CA2DC, the world transform (+0x140) and an indexed triangle list
 * (base vertex, vertex count, triangle count). The iterator and the end are the original's function statics */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00435760(void *self);
DECOMP_C void __thiscall sub_004357F0(void *self);
DECOMP_C char d_006C8C10[], d_006CA2DC[], d_006CA2F4[], d_006CA2F8[], d_006CA2FC[];
typedef void *(__thiscall *vf_4AE3E0)(void *self);
typedef char (__thiscall *vis_4AE3E0)(void *self);
typedef long (__stdcall *dev2_4AE3E0)(void *dev, unsigned int a, void *b);
typedef long (__stdcall *dev1_4AE3E0)(void *dev, void *a);
typedef long (__stdcall *draw_4AE3E0)(void *dev, unsigned int type, int base, unsigned int min, unsigned int n,
                                      unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define IT (*(char ***)d_006CA2F8)
#define END (*(char ***)d_006CA2F4)

DECOMP(004AE3E0)
void __thiscall f_004AE3E0(void *this)
{
    char *s = (char *)this;
    unsigned int g = *(unsigned int *)d_006CA2FC, i;
    void **t;
    char *m;
    if (!(g & 1)) {
        *(unsigned int *)d_006CA2FC = g |= 1;
        IT = 0;
    }
    if (!(g & 2)) {
        *(unsigned int *)d_006CA2FC = g |= 2;
        END = 0;
    }
    if (!*(int *)(s + 0x242c))
        return;
    END = *(char ***)(s + 0x2428);
    t = *(void ***)(s + 0x2430);
    ((dev2_4AE3E0)(*(void ***)DEV)[0x104 / 4])(DEV, 0, ((vf_4AE3E0)(*(void ***)t)[0x28 / 4])(t));
    IT = *(char ***)*(char ***)(s + 0x2428);
    if (IT == END)
        return;
    do {
        m = IT[2];
        if (((vis_4AE3E0)(*(void ***)m)[0x5c / 4])(m)) {
            if (*(unsigned int *)(m + 0x248) & 1)
                sub_00435760(*(void **)(s + 0x2434));
            else if (*(unsigned int *)(m + 0x248) & 2)
                sub_004357F0(*(void **)(s + 0x2434));
            t = *(void ***)(m + 0x244);
            ((dev2_4AE3E0)(*(void ***)DEV)[0x104 / 4])(DEV, 1, ((vf_4AE3E0)(*(void ***)t)[0x28 / 4])(t));
            ((dev2_4AE3E0)(*(void ***)DEV)[0xe4 / 4])(DEV, 0x3c, *(void **)(m + 0x234));
            for (i = 0; i < *(unsigned int *)(m + 0x20c); i++) {
                unsigned int *p = (unsigned int *)(*(char **)(m + 0x208) + i * 12);
                unsigned int base = p[0], n = p[1], cnt = p[2];
                ((dev1_4AE3E0)(*(void ***)DEV)[0x1a0 / 4])(DEV, *(void **)d_006CA2DC);
                ((dev2_4AE3E0)(*(void ***)DEV)[0xb0 / 4])(DEV, 0x100, m + 0x140);
                ((draw_4AE3E0)(*(void ***)DEV)[0x148 / 4])(DEV, 4, base, 0, n, 0, cnt);
            }
        }
        IT = *(char ***)IT;
    } while (IT != END);
}
