/* 0x00478040: creates the two vertex declarations of the mesh once (the dword counter at 0x006CA0A8
 * starts the block: the first passes only stream 0, the second adds stream 2, whose attributes carry
 * usage index 1), stores them through CreateVertexDeclaration (device vtable +0x158) at 0x006CA0A0 and
 * 0x006CA09C and reports each HRESULT through 0x00458940(".\Mesh.cpp", 0x343/0x344); then bumps the
 * counter and, unless the mesh's +0x40 (the vertex-buffer pool) is set, lets 0x00476BB0 fill the
 * buffers.  The second stack argument is not read. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_006C8C10[], d_0060EA44[], d_006CA0A0[], d_006CA09C[], d_006CA0A8[];
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
/* 0x00476BB0: EAX and ECX first, then the two stack arguments (the build gives the call a shim) */
DECOMP_C unsigned int __cdecl sub_00476BB0(unsigned int in_eax, void *this, void *stream, unsigned int flags);

typedef struct {
    unsigned short stream;
    unsigned short offset;
    unsigned char type;
    unsigned char method;
    unsigned char usage;
    unsigned char index;
} vtxelem_478040;

typedef long (__stdcall *create_decl_478040)(void *dev, const vtxelem_478040 *elems, void **decl);

#define VT(o) (*(void ***)(o))

DECOMP(00478040)
void __thiscall f_00478040(void *this, void *stream, void *unused, unsigned int flags)
{
    static const vtxelem_478040 elements[10] = {
        {0, 0,  1, 0, 5, 0},        /* stream 0: TEXCOORD0, float */
        {1, 0,  2, 0, 0, 0},        /* stream 1: POSITION0, float2 */
        {1, 12, 2, 0, 3, 0},        /* stream 1: NORMAL0 at +0xC, float2 */
        {255, 0, 17, 0, 0, 0},      /* end of the stream 0/1 declaration */
        {0, 0,  1, 0, 5, 0},
        {1, 0,  2, 0, 0, 0},
        {1, 12, 2, 0, 3, 0},
        {2, 0,  2, 0, 0, 1},        /* stream 2: POSITION1 */
        {2, 12, 2, 0, 3, 1},        /* stream 2: NORMAL1 */
        {255, 0, 17, 0, 0, 0}
    };
    void **dev;

    if (!*(unsigned int *)d_006CA0A8) {
        dev = *(void ***)d_006C8C10;
        sub_00458940(((create_decl_478040)VT(dev)[0x158 / 4])(dev, elements, (void **)d_006CA0A0),
                     d_0060EA44, 0x343);
        dev = *(void ***)d_006C8C10;
        sub_00458940(((create_decl_478040)VT(dev)[0x158 / 4])(dev, elements + 4, (void **)d_006CA09C),
                     d_0060EA44, 0x344);
    }
    *(unsigned int *)d_006CA0A8 += 1;
    if (!*(unsigned int *)((char *)this + 0x40))
        sub_00476BB0((unsigned int)stream, this, stream, flags);
}
