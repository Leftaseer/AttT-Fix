/* 0x004D8290: recursive subdivision of triangle tri (three vertex indices into the vertex vector +0x3C, 32-byte
 * vertices: position, normal, uv): below the last level (+0x8C against +0x90) each edge gets its midpoint vertex,
 * cached per edge in +0xA4 (0x00481040 / 0x00482540; a new one is the average pushed out along its normal by the
 * level's radius +0x98[level], 0x004D6A60) and the four triangles recurse one level down (the corner ones of the
 * second and third keep the flag); at the last level the triangle goes to the current list (+0x54[+8] group, +0xC
 * list; 0x004D6AD0), split in two at the midpoint of edge 1-2 when the flag is set */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C unsigned short *__thiscall sub_00481040(void *self, unsigned int a, unsigned int b);
DECOMP_C void __thiscall sub_004D6A60(void *self, float *v);
DECOMP_C void __thiscall sub_00482540(void *self, unsigned int a, unsigned int b);
DECOMP_C int __thiscall sub_004D6AD0(void *self, unsigned short *tri);
DECOMP_C void __thiscall f_004D8290(void *self, unsigned short *tri, unsigned int flag);

#define VERTS(s) (*(char **)((s) + 0x3c))

/* the edge (a, b) midpoint's vertex index, made from vertices va and vb when not cached */
static unsigned int mid_4D8290(char *this, unsigned int a, unsigned int b, const float *va, const float *vb)
{
    unsigned short *e = sub_00481040(this + 0xa4, a, b);
    float v[8], p[3], n[3], r;
    char *vec;
    unsigned int idx;
    int i;
    if (*e != 0xffff)
        return *e;
    for (i = 0; i < 3; i++) {
        float s = va[i] + vb[i];
        p[i] = s * 0.5f;
        v[i] = p[i];
    }
    for (i = 0; i < 3; i++) {
        float s = va[3 + i] + vb[3 + i];
        n[i] = s * 0.5f;
        v[3 + i] = n[i];
    }
    v[6] = (va[6] + vb[6]) * 0.5f;
    v[7] = (va[7] + vb[7]) * 0.5f;
    r = (*(float **)(this + 0x98))[*(int *)(this + 0x8c)];
    for (i = 0; i < 3; i++) {
        float t = n[i] * r;
        v[i] = t + p[i];
    }
    vec = VERTS(this);
    idx = *(char **)(vec + 4) ? (unsigned short)((*(char **)(vec + 8) - *(char **)(vec + 4)) >> 5) : 0;
    sub_004D6A60(vec, v);
    *e = (unsigned short)idx;
    sub_00482540(this + 0xa4, a, idx);
    sub_00482540(this + 0xa4, b, idx);
    return idx;
}

/* the current triangle list */
static char *list_4D8290(char *this)
{
    char *g = *(char **)(*(char **)(this + 0x54) + *(int *)(this + 8) * 16 + 4);
    return g + *(int *)(this + 0xc) * 16;
}

DECOMP(004D8290)
void __thiscall f_004D8290(void *self, unsigned short *tri, unsigned int flag)
{
    char *this = (char *)self;
    char *verts = *(char **)(VERTS(this) + 4);
    float v0[8], v1[8], v2[8];
    unsigned short t[3];
    unsigned int m01, m12, m20;

    __builtin_memcpy(v0, verts + tri[0] * 32, 32);
    __builtin_memcpy(v1, verts + tri[1] * 32, 32);
    __builtin_memcpy(v2, verts + tri[2] * 32, 32);
    if (*(int *)(this + 0x8c) == *(int *)(this + 0x90)) {
        if (!(unsigned char)flag) {
            sub_004D6AD0(list_4D8290(this), tri);
            return;
        }
        {
            unsigned short *e = sub_00481040(this + 0xa4, tri[1], tri[2]);
            unsigned int idx;
            if (*e == 0xffff) {
                /* the cache insert order of this split: tri[1], tri[2], then tri[0] */
                float v[8], p[3], n[3], r;
                char *vec;
                int i;
                for (i = 0; i < 3; i++) {
                    float s = v2[i] + v1[i];
                    p[i] = s * 0.5f;
                    v[i] = p[i];
                }
                for (i = 0; i < 3; i++) {
                    float s = v2[3 + i] + v1[3 + i];
                    n[i] = s * 0.5f;
                    v[3 + i] = n[i];
                }
                v[6] = (v2[6] + v1[6]) * 0.5f;
                v[7] = (v2[7] + v1[7]) * 0.5f;
                r = (*(float **)(this + 0x98))[*(int *)(this + 0x8c)];
                for (i = 0; i < 3; i++) {
                    float d = n[i] * r;
                    v[i] = d + p[i];
                }
                vec = VERTS(this);
                idx = *(char **)(vec + 4) ? (unsigned short)((*(char **)(vec + 8) - *(char **)(vec + 4)) >> 5) : 0;
                sub_004D6A60(vec, v);
                *e = (unsigned short)idx;
                sub_00482540(this + 0xa4, tri[1], idx);
                sub_00482540(this + 0xa4, tri[2], idx);
                sub_00482540(this + 0xa4, tri[0], idx);
            } else
                idx = *e;
            sub_004D6AD0(list_4D8290(this), tri);
            (*(unsigned short **)(list_4D8290(this) + 8))[-3 + 2] = (unsigned short)idx;
            sub_004D6AD0(list_4D8290(this), tri);
            (*(unsigned short **)(list_4D8290(this) + 8))[-3 + 1] = (unsigned short)idx;
        }
        return;
    }
    m01 = mid_4D8290(this, tri[0], tri[1], v0, v1);
    m12 = mid_4D8290(this, tri[1], tri[2], v1, v2);
    m20 = mid_4D8290(this, tri[2], tri[0], v2, v0);
    sub_00482540(this + 0xa4, m01, m12);
    sub_00482540(this + 0xa4, m12, m20);
    sub_00482540(this + 0xa4, m20, m01);
    (*(int *)(this + 0x8c))++;
    t[0] = tri[0];
    t[1] = (unsigned short)m01;
    t[2] = (unsigned short)m20;
    f_004D8290(this, t, 0);
    t[0] = (unsigned short)m01;
    t[1] = tri[1];
    t[2] = (unsigned short)m12;
    f_004D8290(this, t, flag);
    t[2] = tri[2];
    t[0] = (unsigned short)m20;
    t[1] = (unsigned short)m12;
    f_004D8290(this, t, flag);
    t[0] = (unsigned short)m01;
    t[1] = (unsigned short)m12;
    t[2] = (unsigned short)m20;
    f_004D8290(this, t, 0);
    (*(int *)(this + 0x8c))--;
}
