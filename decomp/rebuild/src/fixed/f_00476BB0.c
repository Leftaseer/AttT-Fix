/* 0x00476BB0: _ST_ANIM_MESH buffer creation, the animated twin of 0x00476650 (the loader 0x004777F0 fills
 * the same fields): with the low bit of the flags set, every index subset (0x10 bytes at +0x8, count +0xC:
 * index count, data, buffer, file offset) gets a 16-bit index buffer of 6 bytes per index (format 0x65, the
 * usage and pool at +0x44 / +0x40) filled from its data or, when that is null, from the stream after its
 * file (+0x24) vf8 seeks to the entry's offset; then the vertex buffer at +0x2C (+0x24 vertices, 8 bytes
 * each, source +0x28 or offset +0x30) and every entry of the second table (+0x38, +0x34 count, 0xC bytes:
 * data, buffer, offset, 0x18 bytes per vertex) are created and filled the same way.  Creation failures go
 * to 0x00458940(".\Mesh.cpp").  Returns the last Unlock's HRESULT, or the incoming EAX when the flag is
 * clear (the whole body is skipped then). */
/* @conv EAX,ECX 8 */
/* @func 00476BB0 custom */
#include "auto_pre.h"
DECOMP_C char d_006C8C10[], d_0060EA44[];
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */
DECOMP_C void __thiscall sub_00458F80(void *stream, void *dst, unsigned int size);
typedef long (__stdcall *create_476BB0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void **buf, void *shared);
typedef long (__stdcall *lock_476BB0)(void *buf, unsigned int off, unsigned int len, void **data, unsigned int flags);
typedef long (__stdcall *unlock_476BB0)(void *buf);
typedef void (__thiscall *seek_476BB0)(void *self, unsigned int off);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(00476BB0)
unsigned int __cdecl f_00476BB0(unsigned int in_eax, char *this, char *stream, unsigned char flags)
{
    void *data, **b;
    unsigned int i, size;
    long r;
    char *e;

    if (!(flags & 1))
        return in_eax;
    for (i = 0; i < *(unsigned int *)(this + 0xc); i++) {
        e = *(char **)(this + 8) + i * 0x10;
        size = *(unsigned int *)e * 6;
        sub_00458940(((create_476BB0)VT(DEV)[0x6c / 4])(DEV, size, *(unsigned int *)(this + 0x44), 0x65,
                                                        *(unsigned int *)(this + 0x40), (void **)(e + 8), 0),
                     d_0060EA44, 0x24e);
        b = *(void ***)(e + 8);
        ((lock_476BB0)VT(b)[0x2c / 4])(b, 0, size, &data, 0);
        if (*(void **)(e + 4))
            sub_005E4232(data, *(void **)(e + 4), size);
        else {
            void **f = *(void ***)(stream + 0x24);
            ((seek_476BB0)VT(f)[2])(f, *(unsigned int *)(e + 0xc));
            sub_00458F80(stream, data, size);
        }
        b = *(void ***)(e + 8);
        r = ((unlock_476BB0)VT(b)[0x30 / 4])(b);
    }
    size = *(unsigned int *)(this + 0x24) << 3;
    sub_00458940(((create_476BB0)VT(DEV)[0x68 / 4])(DEV, size, *(unsigned int *)(this + 0x44), 0,
                                                    *(unsigned int *)(this + 0x40), (void **)(this + 0x2c), 0),
                 d_0060EA44, 0x260);
    b = *(void ***)(this + 0x2c);
    ((lock_476BB0)VT(b)[0x2c / 4])(b, 0, size, &data, 0);
    if (*(void **)(this + 0x28))
        sub_005E4232(data, *(void **)(this + 0x28), size);
    else {
        void **f = *(void ***)(stream + 0x24);
        ((seek_476BB0)VT(f)[2])(f, *(unsigned int *)(this + 0x30));
        sub_00458F80(stream, data, size);
    }
    b = *(void ***)(this + 0x2c);
    r = ((unlock_476BB0)VT(b)[0x30 / 4])(b);
    for (i = 0; i < *(unsigned int *)(this + 0x34); i++) {
        e = *(char **)(this + 0x38) + i * 0xc;
        size = *(unsigned int *)(this + 0x24) * 0x18;
        sub_00458940(((create_476BB0)VT(DEV)[0x68 / 4])(DEV, size, *(unsigned int *)(this + 0x44), 0,
                                                       *(unsigned int *)(this + 0x40), (void **)(e + 4), 0),
                     d_0060EA44, 0x274);
        b = *(void ***)(e + 4);
        ((lock_476BB0)VT(b)[0x2c / 4])(b, 0, size, &data, 0);
        if (*(void **)e)
            sub_005E4232(data, *(void **)e, size);
        else {
            void **f = *(void ***)(stream + 0x24);
            ((seek_476BB0)VT(f)[2])(f, *(unsigned int *)(e + 8));
            sub_00458F80(stream, data, size);
        }
        b = *(void ***)(e + 4);
        r = ((unlock_476BB0)VT(b)[0x30 / 4])(b);
    }
    return (unsigned int)r;
}
