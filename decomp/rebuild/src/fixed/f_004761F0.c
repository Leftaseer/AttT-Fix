/* 0x004761F0: loads the animated mesh data from a file stream: the subset vector at +0x4 is reset to the
 * leading count, then every entry (0x10 bytes: count +0, data +4, buffer +8, offset +0xC) reads its index
 * count, remembers the reader's current position and, with flag 2, reads count * 6 bytes of 16-bit indices
 * into a new CPU array; with flag 1 an index buffer (format 0x65, usage 8, pool 0) is created, locked,
 * filled from that array (or read straight from the stream) and unlocked, failures going to
 * 0x00458940(".\Mesh.cpp", 0x61).  The first entry's fields are copied to +0x10..+0x20, then the vertex
 * count at +0x24, its stream position (+0x30) and, when positive, the 0x20-byte vertices (position, normal,
 * texcoord) are handled the same way with format 0x112 and line 0x89 (+0x28 array, +0x2C buffer).  The
 * second stack argument is not read. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_006C8C10[], d_0060EA44[];
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                               /* operator new */
DECOMP_C void __thiscall sub_00458F80(void *stream, void *dst, unsigned int size);
DECOMP_C void __thiscall sub_00475E90(void *vector, unsigned int count);              /* reset the subset vector */

typedef long (__stdcall *create_4761F0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void **buf, void *shared);
typedef long (__stdcall *lock_4761F0)(void *buf, unsigned int off, unsigned int len, void **data, unsigned int flags);
typedef long (__stdcall *unlock_4761F0)(void *buf);
typedef unsigned int (__thiscall *tell_4761F0)(void *reader);

typedef struct {
    unsigned int count;     /* +0x0 */
    void *data;             /* +0x4 CPU copy (flag 2) */
    void *buffer;           /* +0x8 device buffer (flag 1) */
    unsigned int offset;    /* +0xC stream position of the data */
} subset_4761F0;

typedef struct {
    void *vtable;               /* +0x0 */
    unsigned int vec_head;      /* +0x4 start of the subset vector */
    subset_4761F0 *subsets;     /* +0x8 vector data */
    unsigned int subset_count;  /* +0xC vector size */
    unsigned int first_count;   /* +0x10 copy of subset 0 */
    unsigned int first_count2;  /* +0x14 */
    void *first_data;           /* +0x18 */
    void *first_buffer;         /* +0x1C */
    unsigned int first_offset;  /* +0x20 */
    unsigned int vertex_count;  /* +0x24 */
    void *vertex_data;          /* +0x28 CPU copy (flag 2) */
    void *vertex_buffer;        /* +0x2C device buffer (flag 1) */
    unsigned int vertex_offset; /* +0x30 stream position of the vertices */
} mesh_4761F0;

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

static unsigned int tell_4761F0_(void *stream)
{
    void **f = *(void ***)((char *)stream + 0x24);
    return ((tell_4761F0)VT(f)[0x10 / 4])(f);
}

DECOMP(004761F0)
void __thiscall f_004761F0(void *this, void *stream, unsigned int unused, unsigned int flags)
{
    mesh_4761F0 *self = this;
    subset_4761F0 *subs;
    unsigned char *data;
    void *b;
    unsigned int count, n, i, j, size;

    sub_00458F80(stream, &count, 4);
    sub_00475E90(&self->vec_head, count);
    subs = self->subsets;
    for (i = 0; i < count; i++) {
        self->subset_count += 1;
        sub_00458F80(stream, &n, 4);
        subs[i].count = n;
        if (!n)
            continue;
        subs[i].offset = tell_4761F0_(stream);
        if (flags & 2) {
            subs[i].data = sub_005E3B10(n * 6);
            sub_00458F80(stream, subs[i].data, n * 6);
        }
        if (flags & 1) {
            size = n * 6;
            sub_00458940(((create_4761F0)VT(DEV)[0x6c / 4])(DEV, size, 8, 0x65, 0, &subs[i].buffer, 0),
                         d_0060EA44, 0x61);
            b = subs[i].buffer;
            ((lock_4761F0)VT(b)[0x2c / 4])(b, 0, size, (void **)&data, 0);
            if (subs[i].data)
                sub_005E4232(data, subs[i].data, size);
            else
                sub_00458F80(stream, data, size);
            b = subs[i].buffer;
            ((unlock_4761F0)VT(b)[0x30 / 4])(b);
        }
    }
    subs = self->subsets;
    self->first_count = subs[0].count;
    self->first_count2 = subs[0].count;
    self->first_data = subs[0].data;
    self->first_buffer = subs[0].buffer;
    self->first_offset = subs[0].offset;

    sub_00458F80(stream, &self->vertex_count, 4);
    if (self->vertex_count) {
        self->vertex_offset = tell_4761F0_(stream);
        if (flags & 2) {
            data = sub_005E3B10(self->vertex_count * 0x20);
            for (j = 0; j < self->vertex_count * 0x20; j++)
                data[j] = 0;
            self->vertex_data = data;
            sub_00458F80(stream, data, self->vertex_count * 0x20);
        }
        if (flags & 1) {
            size = self->vertex_count * 0x20;
            sub_00458940(((create_4761F0)VT(DEV)[0x68 / 4])(DEV, size, 8, 0x112, 0, &self->vertex_buffer, 0),
                         d_0060EA44, 0x89);
            b = self->vertex_buffer;
            ((lock_4761F0)VT(b)[0x2c / 4])(b, 0, size, (void **)&data, 0);
            if (self->vertex_data)
                sub_005E4232(data, self->vertex_data, size);
            else
                sub_00458F80(stream, data, size);
            b = self->vertex_buffer;
            ((unlock_4761F0)VT(b)[0x30 / 4])(b);
        }
    }
}
