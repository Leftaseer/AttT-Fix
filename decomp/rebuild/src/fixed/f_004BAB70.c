/* 0x004BAB70: NSkinAnimation::CSkeletonMeshSubObject::Draw2: poses the skeleton from the animation set (arg 1, its
 * track +0xD4) at the frame (arg 2, 0 past the track's frame count: 0x004B9110 on the frame's 24-byte keys), skins
 * the vertices (0x004BA7F0 on +0xD8), sets the index buffer (+0xFC) and the vertex buffer (+0xEC, 0x004BA550; 32-byte
 * vertices), the texture (arg 4, if any) and, per pass of the effect (arg 3: vf18 begin, vf20 / vf24 per pass, vf1C
 * end), each subset (+0x08..+0x0C, 0x6C bytes): its material, its own texture (+0x60) when arg 4 is null and the
 * effect's +0x38 is 0, and an indexed triangle list (+0x64 first index, +0x68 triangles) over the vertices
 * (+0xDC..+0xE0, 32 bytes each); returns 0x004BA4D0 on the vertex buffer */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B9110(void *self, void *keys);
DECOMP_C void __thiscall sub_004BA7F0(void *self, void *verts);
DECOMP_C void **__thiscall sub_004BA550(void *self);
DECOMP_C int __thiscall sub_004BA4D0(void *self);
DECOMP_C char d_006C8C10[];
typedef void *(__thiscall *vf_4BAB70)(void *self);
typedef void (__thiscall *begin_4BAB70)(void *self, unsigned int *passes, int flags);
typedef void (__thiscall *pass_4BAB70)(void *self, unsigned int i);
typedef long (__stdcall *dev1_4BAB70)(void *dev, void *a);
typedef long (__stdcall *dev2_4BAB70)(void *dev, unsigned int a, void *b);
typedef long (__stdcall *src_4BAB70)(void *dev, unsigned int stream, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *draw_4BAB70)(void *dev, unsigned int type, int base, unsigned int min, unsigned int n,
                                      unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)

DECOMP(004BAB70)
int __thiscall f_004BAB70(void *this, char *set, unsigned int frame, void **fx, void **tex)
{
    char *s = (char *)this;
    unsigned int idx = *(unsigned int *)(s + 0xd4), passes, i, n;
    char *v = *(char **)(set + 4), *sub;
    unsigned int *trk;
    void **t;
    trk = v && idx < (unsigned int)(*(char **)(set + 8) - v) >> 2 ? ((unsigned int **)v)[idx] : 0;
    if (frame >= trk[2])
        frame = 0;
    sub_004B9110(this, (char *)trk[0] + trk[3] * frame * 0x18);
    sub_004BA7F0(this, s + 0xd8);
    ((dev1_4BAB70)(*(void ***)DEV)[0x1a0 / 4])(DEV, *(void **)(s + 0xfc));
    ((src_4BAB70)(*(void ***)DEV)[0x190 / 4])(DEV, 0, *sub_004BA550(s + 0xec), 0, 0x20);
    if (tex)
        ((dev2_4BAB70)(*(void ***)DEV)[0x104 / 4])(DEV, 0, ((vf_4BAB70)(*(void ***)tex)[0x28 / 4])(tex));
    ((begin_4BAB70)(*(void ***)fx)[0x18 / 4])(fx, &passes, 0);
    for (i = 0; i < passes; i++) {
        ((pass_4BAB70)(*(void ***)fx)[0x20 / 4])(fx, i);
        for (sub = *(char **)(s + 8); sub != *(char **)(s + 0xc); sub += 0x6c) {
            ((dev1_4BAB70)(*(void ***)DEV)[0xc4 / 4])(DEV, sub);
            if (*(void **)(sub + 0x60) && !tex && !((int *)fx)[0xe]) {
                t = *(void ***)(sub + 0x60);
                ((dev2_4BAB70)(*(void ***)DEV)[0x104 / 4])(DEV, 0, ((vf_4BAB70)(*(void ***)t)[0x28 / 4])(t));
            }
            n = *(char **)(s + 0xdc) ? (unsigned int)((*(int *)(s + 0xe0) - *(int *)(s + 0xdc)) >> 5) : 0;
            ((draw_4BAB70)(*(void ***)DEV)[0x148 / 4])(DEV, 4, 0, 0, n, *(unsigned short *)(sub + 0x64),
                                                       *(unsigned int *)(sub + 0x68));
        }
        ((vf_4BAB70)(*(void ***)fx)[0x24 / 4])(fx);
    }
    ((vf_4BAB70)(*(void ***)fx)[0x1c / 4])(fx);
    return sub_004BA4D0(s + 0xec);
}
