/* 0x004CF960: CSurfacePlane buffer setup: releases any previous vertex and index buffers (+0x70, +0x74),
 * then creates a 20-byte-stride vertex buffer for the +0x80 vertices and a 16-bit index buffer of
 * 6 * (vertices / 3) bytes (FVF 0x102 / D3DFMT_INDEX16, managed) on the global D3D device and copies the
 * +0x78 vertices and +0x7C indices through lock/unlock.  Creation failures go to 0x00458940 with
 * ".\\SurfacePlane.cpp". */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP_C char d_006C8C10[], d_00611FE0[];
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */

typedef long (__stdcall *create_4CF960)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_4CF960)(void *self, unsigned int off, unsigned int size, void **data,
                                      unsigned int fl);
typedef long (__stdcall *com_4CF960)(void *self);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))
#define SURFACEPLANE_CPP (d_00611FE0 + 0x10)      /* ".\\SurfacePlane.cpp" */

DECOMP(004CF960)
void __thiscall f_004CF960(char *this)
{
    void *data;
    unsigned int count;

    if (*(void **)(this + 0x70)) {
        void *vb = *(void **)(this + 0x70);
        ((com_4CF960)VT(vb)[0x8 / 4])(vb);
        *(void **)(this + 0x70) = 0;
    }
    if (*(void **)(this + 0x74)) {
        void *ib = *(void **)(this + 0x74);
        ((com_4CF960)VT(ib)[0x8 / 4])(ib);
        *(void **)(this + 0x74) = 0;
    }
    count = *(unsigned int *)(this + 0x80);
    sub_00458940(((create_4CF960)VT(DEV)[0x68 / 4])(DEV, count * 20, 8, 0x102, 1, this + 0x70, 0),
                 SURFACEPLANE_CPP, 0x78);
    data = 0;
    ((lock_4CF960)VT(*(void **)(this + 0x70))[0x2c / 4])(*(void **)(this + 0x70), 0, 0, &data, 0);
    sub_005E4232(data, *(void **)(this + 0x78), count * 20);
    ((com_4CF960)VT(*(void **)(this + 0x70))[0x30 / 4])(*(void **)(this + 0x70));
    sub_00458940(((create_4CF960)VT(DEV)[0x6c / 4])(DEV, (count / 3) * 6, 8, 0x65, 1, this + 0x74, 0),
                 SURFACEPLANE_CPP, 0x83);
    data = 0;
    ((lock_4CF960)VT(*(void **)(this + 0x74))[0x2c / 4])(*(void **)(this + 0x74), 0, 0, &data, 0);
    sub_005E4232(data, *(void **)(this + 0x7c), count * 2);
    ((com_4CF960)VT(*(void **)(this + 0x74))[0x30 / 4])(*(void **)(this + 0x74));
}
