/* 0x00476650: ST_STATIC_MESH::vf6(stream, flags): with flag 1 creates its buffers: per subset (16 bytes at +8,
 * count +0xC: index count, data, buffer, file offset) a 16-bit index buffer (CreateIndexBuffer(n * 6, WRITEONLY,
 * D3DFMT_INDEX16)) filled from memory or read from the stream (its file +0x24 vf08 seeks, 0x00458F80 reads), and the
 * 32-byte vertex buffer (+0x24 vertices, +0x28 data or +0x30 offset, into +0x2C); the first subset is copied to
 * +0x10..+0x20; returns what the vertex buffer's Unlock returned */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void __thiscall sub_00458F80(void *stream, void *dst, unsigned int size);
DECOMP_C void *(__cdecl *imp_00607424)(void *, const void *, unsigned int) __asm__("__imp__memcpy");
DECOMP_C char d_006C8C10[], d_0060EA44[];
typedef long (__stdcall *CreateBuf_476650)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                           unsigned int pool, void **buf, void *shared);
typedef long (__stdcall *Lock_476650)(void *buf, unsigned int off, unsigned int len, void **data, unsigned int flags);
typedef long (__stdcall *Unlock_476650)(void *buf);
typedef void (__thiscall *seek_476650)(void *self, unsigned int off);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(00476650)
unsigned int __thiscall f_00476650(void *this, char *stream, unsigned int flags)
{
    char *s = (char *)this;
    unsigned int i, *e, size;
    void *data, **b;
    for (i = 0; i < *(unsigned int *)(s + 0xc); i++) {
        e = (unsigned int *)(*(char **)(s + 8) + i * 0x10);
        if (!e[0] || !(flags & 1))
            continue;
        size = e[0] * 6;
        sub_00458940(((CreateBuf_476650)VT(DEV)[0x6c / 4])(DEV, size, 8, 0x65, 0, (void **)(e + 2), 0),
                     d_0060EA44, 0xd5);
        b = (void **)(*(unsigned int **)(s + 8))[i * 4 + 2];
        ((Lock_476650)VT(b)[0x2c / 4])(b, 0, size, &data, 0);
        e = (unsigned int *)(*(char **)(s + 8) + i * 0x10);
        if (e[1])
            imp_00607424(data, (void *)e[1], size);
        else {
            void **f = *(void ***)(stream + 0x24);
            ((seek_476650)VT(f)[2])(f, e[3]);
            sub_00458F80(stream, data, size);
        }
        b = (void **)(*(unsigned int **)(s + 8))[i * 4 + 2];
        ((Unlock_476650)VT(b)[0x30 / 4])(b);
    }
    e = *(unsigned int **)(s + 8);
    *(unsigned int *)(s + 0x10) = e[0];
    *(unsigned int *)(s + 0x14) = e[0];
    *(unsigned int *)(s + 0x18) = e[1];
    *(unsigned int *)(s + 0x1c) = e[2];
    *(unsigned int *)(s + 0x20) = e[3];
    if (!*(unsigned int *)(s + 0x24) || !(flags & 1))
        return *(unsigned int *)(s + 0x24);
    sub_00458940(((CreateBuf_476650)VT(DEV)[0x68 / 4])(DEV, *(unsigned int *)(s + 0x24) << 5, 8, 0x112, 0,
                                                       (void **)(s + 0x2c), 0), d_0060EA44, 0xf5);
    b = *(void ***)(s + 0x2c);
    ((Lock_476650)VT(b)[0x2c / 4])(b, 0, *(unsigned int *)(s + 0x24) << 5, &data, 0);
    if (*(void **)(s + 0x28))
        imp_00607424(data, *(void **)(s + 0x28), *(unsigned int *)(s + 0x24) << 5);
    else {
        void **f = *(void ***)(stream + 0x24);
        ((seek_476650)VT(f)[2])(f, *(unsigned int *)(s + 0x30));
        sub_00458F80(stream, data, *(unsigned int *)(s + 0x24) << 5);
    }
    b = *(void ***)(s + 0x2c);
    return ((Unlock_476650)VT(b)[0x30 / 4])(b);
}
