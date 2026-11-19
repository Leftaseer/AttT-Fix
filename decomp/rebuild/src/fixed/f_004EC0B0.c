/* 0x004EC0B0 (ECX = a ground plane, args: an int forwarded to the vtable slot 0x28, the column count, the row
 * count, a byte flag; ret 0x10): zeroes the vectors at +0x58 and +0x68, sets the +0x70 triple to 1.0, makes the
 * four matrices at +0x80, +0xC0, +0x100 and +0x140 identities, clears +0x180 and stores the flag at +0x1A6; then
 * the vtable slot 0x28 runs with the first int, the sizes land in +0x184 (columns) and +0x188 (rows), the old
 * vertex array +0x19C is deleted and rows*columns 12-byte vertices are allocated for it (+0x1A0 is their count).
 * The grid is rows*rows points: (j*sx - 0.5, 0, i*sz - 0.5) with sx = 1/(columns-1) and sz = 1/(rows-1) (both
 * divisions are unsigned; the original spreads both axes over the row count, only the index grid below uses the
 * columns).  A 20-byte vertex buffer (usage 8, FVF 0x006C09F8, pool 1, +0x18C, device 0x006C8C10 slot 0x68) gets
 * u = x + 0.5 and v = 1 - (z + 0.5) written at +0x0C/+0x10 of every entry, then a 16-bit index buffer of
 * (rows-1)*(columns-1) quads (usage 8, format 0x65, pool 1, +0x190, count*2 at +0x194) is filled with the six
 * indices a, b, a+1, b, b+1, a+1 per quad (a = row*columns + column, b = a + columns, all 16-bit), where the
 * repeated b makes the second triangle degenerate but is what the original stores.  Both buffers are locked (slot 0x2C) and
 * unlocked (slot 0x30), creation failures go to 0x00458940("e:\prog\att1\GroundPlane.h", 0xD4/0xE6) and the
 * ready bytes +0x1A4/+0x1A5 are set to 1. */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                             /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *block);                                    /* operator delete[] */
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C char d_00612BC8[], d_006C8C10[], d_006C09F8[];

typedef void (__thiscall *init_4EC0B0)(void *self, int arg);
typedef long (__stdcall *create_4EC0B0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void **buf, void *shared);
typedef long (__stdcall *lock_4EC0B0)(void *buf, unsigned int off, unsigned int len, void **data, unsigned int flags);
typedef long (__stdcall *unlock_4EC0B0)(void *buf);

#define DEV_4EC0B0 (*(void ***)d_006C8C10)
#define VT_4EC0B0(o) (*(void ***)(o))
#define FVF_4EC0B0 (*(unsigned int *)d_006C09F8)

DECOMP(004EC0B0)
void __thiscall f_004EC0B0(void *this, int arg, int width, int height, unsigned char flag)
{
    char *s = (char *)this;
    void *vb, *ib, *vlock = 0, *ilock = 0;
    unsigned int i, j, k, count = 0, n, rows, cols;
    float sx, sz;

    *(char *)(s + 0x1a6) = (char)flag;
    *(float *)(s + 0x178) = 0.0f;
    *(float *)(s + 0x174) = 0.0f;
    *(float *)(s + 0x170) = 0.0f;
    *(float *)(s + 0x16c) = 0.0f;
    *(float *)(s + 0x164) = 0.0f;
    *(float *)(s + 0x160) = 0.0f;
    *(float *)(s + 0x15c) = 0.0f;
    *(float *)(s + 0x158) = 0.0f;
    *(float *)(s + 0x150) = 0.0f;
    *(float *)(s + 0x14c) = 0.0f;
    *(float *)(s + 0x148) = 0.0f;
    *(float *)(s + 0x144) = 0.0f;
    *(float *)(s + 0x17c) = 1.0f;
    *(float *)(s + 0x168) = 1.0f;
    *(float *)(s + 0x154) = 1.0f;
    *(float *)(s + 0x140) = 1.0f;
    *(char *)(s + 0x180) = 0;
    *(float *)(s + 0x58) = 0.0f;
    *(float *)(s + 0x5c) = 0.0f;
    *(float *)(s + 0x60) = 0.0f;
    *(char *)(s + 0x64) = 0;
    *(float *)(s + 0xb8) = 0.0f;
    *(float *)(s + 0xb4) = 0.0f;
    *(float *)(s + 0xb0) = 0.0f;
    *(float *)(s + 0xac) = 0.0f;
    *(float *)(s + 0xa4) = 0.0f;
    *(float *)(s + 0xa0) = 0.0f;
    *(float *)(s + 0x9c) = 0.0f;
    *(float *)(s + 0x98) = 0.0f;
    *(float *)(s + 0x90) = 0.0f;
    *(float *)(s + 0x8c) = 0.0f;
    *(float *)(s + 0x88) = 0.0f;
    *(float *)(s + 0x84) = 0.0f;
    *(float *)(s + 0xbc) = 1.0f;
    *(float *)(s + 0xa8) = 1.0f;
    *(float *)(s + 0x94) = 1.0f;
    *(float *)(s + 0x80) = 1.0f;
    *(float *)(s + 0x68) = 0.0f;
    *(char *)(s + 0x6c) = 0;
    *(float *)(s + 0xf8) = 0.0f;
    *(float *)(s + 0xf4) = 0.0f;
    *(float *)(s + 0xf0) = 0.0f;
    *(float *)(s + 0xec) = 0.0f;
    *(float *)(s + 0xe4) = 0.0f;
    *(float *)(s + 0xe0) = 0.0f;
    *(float *)(s + 0xdc) = 0.0f;
    *(float *)(s + 0xd8) = 0.0f;
    *(float *)(s + 0xd0) = 0.0f;
    *(float *)(s + 0xcc) = 0.0f;
    *(float *)(s + 0xc8) = 0.0f;
    *(float *)(s + 0xc4) = 0.0f;
    *(float *)(s + 0xfc) = 1.0f;
    *(float *)(s + 0xe8) = 1.0f;
    *(float *)(s + 0xd4) = 1.0f;
    *(float *)(s + 0xc0) = 1.0f;
    *(float *)(s + 0x70) = 1.0f;
    *(float *)(s + 0x74) = 1.0f;
    *(float *)(s + 0x78) = 1.0f;
    *(char *)(s + 0x7c) = 0;
    *(float *)(s + 0x138) = 0.0f;
    *(float *)(s + 0x134) = 0.0f;
    *(float *)(s + 0x130) = 0.0f;
    *(float *)(s + 0x12c) = 0.0f;
    *(float *)(s + 0x124) = 0.0f;
    *(float *)(s + 0x120) = 0.0f;
    *(float *)(s + 0x11c) = 0.0f;
    *(float *)(s + 0x118) = 0.0f;
    *(float *)(s + 0x110) = 0.0f;
    *(float *)(s + 0x10c) = 0.0f;
    *(float *)(s + 0x108) = 0.0f;
    *(float *)(s + 0x104) = 0.0f;
    *(float *)(s + 0x13c) = 1.0f;
    *(float *)(s + 0x128) = 1.0f;
    *(float *)(s + 0x114) = 1.0f;
    *(float *)(s + 0x100) = 1.0f;
    ((init_4EC0B0)VT_4EC0B0(s)[0x28 / 4])(s, arg);
    *(int *)(s + 0x184) = width;
    *(int *)(s + 0x188) = height;
    n = (unsigned int)width * (unsigned int)height;
    if (*(void **)(s + 0x19c)) {
        sub_005E3EBA(*(void **)(s + 0x19c));
        *(void **)(s + 0x19c) = 0;
    }
    if (n) {
        unsigned long long bytes = (unsigned long long)n * 0xc;
        *(void **)(s + 0x19c) = sub_005E3B10(bytes > 0xffffffffu ? 0xffffffffu : (unsigned int)bytes);
    }
    *(unsigned int *)(s + 0x1a0) = 0;
    sx = (float)(1.0 / (double)((unsigned int)width - 1));
    sz = (float)(1.0 / (double)((unsigned int)height - 1));
    rows = (unsigned int)height;
    for (i = 0; i < rows; i++) {
        for (j = 0; j < rows; j++) {
            float *v = (float *)(*(char **)(s + 0x19c) + count * 0xc);
            v[0] = (float)((double)j * (double)sx - 0.5);
            v[1] = 0.0f;
            v[2] = (float)((double)i * (double)sz - 0.5);
            count++;
        }
    }
    *(unsigned int *)(s + 0x1a0) = count;
    sub_00458940(((create_4EC0B0)VT_4EC0B0(DEV_4EC0B0)[0x68 / 4])(DEV_4EC0B0, count * 0x14, 8, FVF_4EC0B0, 1,
                    (void **)(s + 0x18c), 0), d_00612BC8, 0xd4);
    vb = *(void **)(s + 0x18c);
    ((lock_4EC0B0)VT_4EC0B0(vb)[0x2c / 4])(vb, 0, 0, &vlock, 0);
    for (k = 0; k < count; k++) {
        float *v = (float *)(*(char **)(s + 0x19c) + k * 0xc);
        char *o = (char *)vlock + k * 0x14;
        *(float *)(o + 0x0c) = (float)((double)v[0] + 0.5);
        *(float *)(o + 0x10) = (float)(1.0 - ((double)v[2] + 0.5));
    }
    ((unlock_4EC0B0)VT_4EC0B0(vb)[0x30 / 4])(vb);
    rows = (unsigned int)height - 1;
    cols = (unsigned int)width - 1;
    n = rows * cols;
    *(unsigned int *)(s + 0x194) = n * 2;
    sub_00458940(((create_4EC0B0)VT_4EC0B0(DEV_4EC0B0)[0x6c / 4])(DEV_4EC0B0, n * 0xc, 8, 0x65, 1,
                    (void **)(s + 0x190), 0), d_00612BC8, 0xe6);
    ib = *(void **)(s + 0x190);
    ((lock_4EC0B0)VT_4EC0B0(ib)[0x2c / 4])(ib, 0, 0, &ilock, 0);
    {
        unsigned short *out = (unsigned short *)ilock;
        if (rows) {
            for (i = 0; i < rows; i++) {
                if (!cols)
                    continue;
                for (j = 0; j < cols; j++) {
                    unsigned short ii = (unsigned short)i, jj = (unsigned short)j;
                    unsigned short a = (unsigned short)((unsigned short)width * ii + jj);
                    unsigned short b = (unsigned short)((unsigned short)width * (unsigned short)(ii + 1) + jj);
                    out[0] = a;
                    out[1] = b;
                    out[2] = (unsigned short)(a + 1);
                    out[3] = b;
                    out[4] = (unsigned short)(b + 1);
                    out[5] = (unsigned short)(a + 1);
                    out += 6;
                }
            }
        }
    }
    ((unlock_4EC0B0)VT_4EC0B0(ib)[0x30 / 4])(ib);
    *(char *)(s + 0x1a4) = 1;
    *(char *)(s + 0x1a5) = 1;
}
