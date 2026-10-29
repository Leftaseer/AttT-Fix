/* 0x004D7AC0: subdivides a triangle of vertex indices (vertices of 0x20 bytes: position, normal, uv in the list
 * +0x3C): each edge gets one midpoint vertex, shared through the edge map +0xA4 (0x00481040 slot, 0xFFFF when new),
 * whose position is the averaged position pushed out along the averaged normal by the radius of this level (+0x98
 * [+0x8C]); the new edges are linked (0x00482540); at the last level (+0x90) the 4 triangles go to the index list of
 * the current part (+0x54 [+8] +4, [+0xC], 0x004D6AD0), otherwise each is subdivided again */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned short *__thiscall sub_00481040(void *self, unsigned int a, unsigned int b);
DECOMP_C void __thiscall sub_004D6A60(void *self, float *v);
DECOMP_C void __thiscall sub_00482540(void *self, unsigned int a, unsigned int b);
DECOMP_C int __thiscall sub_004D6AD0(void *self, unsigned short *tri);

/* index of the midpoint vertex of the edge (a, b) */
static unsigned int mid_4D7AC0(char *this, const unsigned short *tri, int ia, int ib, const float *a, const float *b)
{
    unsigned short *slot = sub_00481040(this + 0xa4, tri[ia], tri[ib]);
    float v[8], m[3], n[3], r;
    char *list;
    unsigned int idx;
    int i;
    if (*slot != 0xffff)
        return *slot;
    for (i = 0; i < 3; i++) {
        float s = (float)((long double)b[i] + a[i]);
        m[i] = (float)(s * 0.5);
        v[i] = m[i];
    }
    for (i = 0; i < 3; i++) {
        float s = (float)((long double)b[3 + i] + a[3 + i]);
        n[i] = (float)(s * 0.5);
        v[3 + i] = n[i];
    }
    v[6] = (float)(((long double)b[6] + a[6]) * 0.5);
    v[7] = (float)(((long double)b[7] + a[7]) * 0.5);
    r = (*(float **)(this + 0x98))[*(int *)(this + 0x8c)];
    for (i = 0; i < 3; i++)
        v[i] = (float)((long double)(float)((long double)n[i] * r) + m[i]);
    list = *(char **)(this + 0x3c);
    idx = *(char **)(list + 4) ? (unsigned short)((*(char **)(list + 8) - *(char **)(list + 4)) >> 5) : 0;
    sub_004D6A60(list, v);
    *slot = (unsigned short)idx;
    sub_00482540(this + 0xa4, tri[ia], idx);
    sub_00482540(this + 0xa4, tri[ib], idx);
    return idx;
}

DECOMP(004D7AC0)
int __thiscall f_004D7AC0(char *this, unsigned short *tri)
{
    char *verts = *(char **)(*(char **)(this + 0x3c) + 4);
    float v0[8], v1[8], v2[8];
    unsigned int i01, i12, i20;
    unsigned short t[3];
    int r;

    __builtin_memcpy(v0, verts + tri[0] * 0x20, 0x20);
    __builtin_memcpy(v1, verts + tri[1] * 0x20, 0x20);
    __builtin_memcpy(v2, verts + tri[2] * 0x20, 0x20);
    i01 = mid_4D7AC0(this, tri, 0, 1, v0, v1);
    i12 = mid_4D7AC0(this, tri, 1, 2, v1, v2);
    i20 = mid_4D7AC0(this, tri, 2, 0, v2, v0);
    sub_00482540(this + 0xa4, i01, i12);
    sub_00482540(this + 0xa4, i12, i20);
    sub_00482540(this + 0xa4, i20, i01);

    if (++*(int *)(this + 0x8c) == *(int *)(this + 0x90)) {
        char *out = *(char **)(*(char **)(this + 0x54) + *(int *)(this + 8) * 0x10 + 4) + *(int *)(this + 0xc) * 0x10;
        t[0] = tri[0]; t[1] = (unsigned short)i01; t[2] = (unsigned short)i20;
        sub_004D6AD0(out, t);
        t[0] = (unsigned short)i01; t[1] = tri[1]; t[2] = (unsigned short)i12;
        sub_004D6AD0(out, t);
        t[0] = (unsigned short)i12; t[1] = tri[2]; t[2] = (unsigned short)i20;
        sub_004D6AD0(out, t);
        t[0] = (unsigned short)i01; t[1] = (unsigned short)i12; t[2] = (unsigned short)i20;
        r = sub_004D6AD0(out, t);
    } else {
        t[0] = tri[0]; t[1] = (unsigned short)i01; t[2] = (unsigned short)i20;
        f_004D7AC0(this, t);
        t[0] = (unsigned short)i01; t[1] = tri[1]; t[2] = (unsigned short)i12;
        f_004D7AC0(this, t);
        t[0] = (unsigned short)i12; t[1] = tri[2]; t[2] = (unsigned short)i20;
        f_004D7AC0(this, t);
        t[0] = (unsigned short)i01; t[1] = (unsigned short)i12; t[2] = (unsigned short)i20;
        r = f_004D7AC0(this, t);
    }
    (*(int *)(this + 0x8c))--;
    return r;
}
