/* 0x00557370: builds a forest's buffers: for its +0x10 trees, a write-only vertex buffer (+0x08: 32-byte vertices
 * of FVF 0x112, the mesh's 0x006CAB0C vertices per tree) and an index buffer (+0x0C: 16-bit, 0x006CAB08 triangles per
 * tree), failures reported to 0x00458940 with ".\Forests.cpp"; each tree (+0x18..+0x1C, 0x48 bytes: the mesh's
 * group and index, then its matrix) puts the mesh's vertices (the tree mesh list 0x006C5368) through the matrix
 * (D3DXVec3TransformCoord), the normals through its inverse transpose (D3DXMatrixTranspose, D3DXMatrixInverse,
 * D3DXVec3TransformNormal) and copies the texture coordinates; unlocked, returns 0x00556F90 (which also takes the
 * Unlock result in EAX); 0 with no trees */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C void *__stdcall sub_005B80E0(void *out, const void *m);                     /* D3DXMatrixTranspose */
DECOMP_C void *__stdcall sub_005B801A(void *out, float *det, const void *m);         /* D3DXMatrixInverse */
DECOMP_C float *__stdcall sub_005B808C(float *out, const float *v, const void *m);   /* D3DXVec3TransformNormal */
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C int __cdecl sub_00556F90(void *self, long eax);
DECOMP_C char d_006C8C10[], d_006CAB08[], d_006CAB0C[], d_006C5368[], d_0061BE44[];
typedef long (__stdcall *create_557370)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_557370)(void *self, unsigned int off, unsigned int size, char **data, unsigned int fl);
typedef long (__stdcall *com_557370)(void *self);

#define DEV (*(void ***)d_006C8C10)
#define NV (*(unsigned int *)d_006CAB0C)

DECOMP(00557370)
int __thiscall f_00557370(void *this)
{
    char *s = (char *)this;
    char *vb, *it, *mesh, *d, *v;
    unsigned int m[16], mi[16], n = 0, j;
    void **buf;
    if (!*(unsigned int *)(s + 0x10))
        return 0;
    sub_00458940(((create_557370)(*(void ***)DEV)[0x68 / 4])(DEV, *(unsigned int *)(s + 0x10) * NV << 5, 8, 0x112, 0,
                                                              s + 8, 0),
                 d_0061BE44, 0x135);
    sub_00458940(((create_557370)(*(void ***)DEV)[0x6c / 4])(DEV, *(unsigned int *)(s + 0x10) *
                                                                   *(unsigned int *)d_006CAB08 * 6,
                                                              8, 0x65, 0, s + 0xc, 0),
                 d_0061BE44, 0x138);
    buf = *(void ***)(s + 8);
    ((lock_557370)(*(void ***)buf)[0x2c / 4])(buf, 0, 0, &vb, 0);
    for (it = *(char **)(s + 0x18); it != *(char **)(s + 0x1c); it += 0x48) {
        char *grp = *(char **)(*(char **)(*(char **)d_006C5368 + 4) + *(int *)it * 12 + 4);
        mesh = *(char **)(grp + *(int *)(it + 4) * 0x4c + 0x20);
        __builtin_memcpy(m, it + 8, 64);
        for (j = 0; j < NV; j++) {
            d = vb + ((n & 0xffff) << 5);
            sub_005B8026((float *)d, (float *)(*(char **)(mesh + 0x28) + j * 0x20), m);
            sub_005B80E0(mi, m);
            sub_005B801A(mi, 0, mi);
            sub_005B808C((float *)(d + 0xc), (float *)(*(char **)(mesh + 0x28) + j * 0x20 + 0xc), mi);
            n++;
            v = *(char **)(mesh + 0x28) + j * 0x20;
            *(float *)(d + 0x18) = *(float *)(v + 0x18);
            v = *(char **)(mesh + 0x28) + j * 0x20;
            *(float *)(d + 0x1c) = *(float *)(v + 0x1c);
        }
    }
    buf = *(void ***)(s + 8);
    return sub_00556F90(this, ((com_557370)(*(void ***)buf)[0x30 / 4])(buf));
}
