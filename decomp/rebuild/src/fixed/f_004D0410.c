/* 0x004D0410: build the textured triangle list of a ground decal: the mesh (+0x60) triangles near (+0x64, 0, +0x68)
 * within 100 (0x00452F00) become 2D polygons (x,z) in a vector; 0x004CFE10 clips them against the +0x58 outline into
 * a list of polygons; each clipped point gets its height from the triangle that contains it (0x00480A30,
 * 0x004CFC30, raised by 0.01) and its UV from the matrix (D3DXVec2Transform) as |p - (+0x84,+0x88)| / (+0x8C,+0x90);
 * the vertices (0x14 bytes) go to a new[] array in *out and their count to *count; all polygons are freed */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C unsigned short *__thiscall sub_00452F00(void *mesh, float *pos, float radius, unsigned *count);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void __cdecl sub_005E3E9C(void *p);                                   /* operator delete */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                        /* operator new[] */
DECOMP_C void *__thiscall sub_0043BBC0(void *self);
DECOMP_C float *__thiscall sub_004205A0(float *self, float x, float y);
DECOMP_C void __thiscall sub_0047F760(void *self, void *pt);
DECOMP_C void __thiscall sub_00487860(void *self, void *where, unsigned int n, void *val);
DECOMP_C char *__thiscall sub_004CFE10(void *self, void *outline, void *polys);
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C float *__thiscall sub_0047F6E0(void *poly);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);
DECOMP_C unsigned char __cdecl sub_00480A30(void *eax, void *poly, void *pt);
DECOMP_C void __thiscall sub_0047F690(void *self);
DECOMP_C float *__stdcall sub_005B80A4(float *out, const float *v, const void *m);   /* D3DXVec2Transform */
DECOMP_C char d_00608B4C[];

typedef struct { float x, y, z; } V3_4D0410;
DECOMP_C void __stdcall sub_004CFC30(float *out, V3_4D0410 a, V3_4D0410 b, V3_4D0410 c, float *pt);

typedef struct { void *alloc; void **begin, **end, **cap; } Vec_4D0410;

DECOMP(004D0410)
void __thiscall f_004D0410(char *this, float **out, int *count, void *matrix)
{
    Vec_4D0410 polys = { 0, 0, 0, 0 };
    float pos[3], tmp[2];
    unsigned ntri, i;
    unsigned short *idx;
    V3_4D0410 *verts = *(V3_4D0410 **)(*(char **)(this + 0x60) + 0x24);
    char *res, **head, **node;
    int j;

    pos[0] = *(float *)(this + 0x64);
    pos[1] = 0.0f;
    pos[2] = *(float *)(this + 0x68);
    idx = sub_00452F00(*(void **)(this + 0x60), pos, *(float *)d_00608B4C, &ntri);
    for (i = 0; i < ntri; i++) {
        unsigned short *t = idx + i * 3;
        void *mem = sub_005E3EAE(8), *poly = 0;
        V3_4D0410 a, b, c;
        if (mem)
            poly = sub_0043BBC0(mem);
        a = verts[t[0]];
        b = verts[t[1]];
        c = verts[t[2]];
        sub_0047F760(poly, sub_004205A0(tmp, a.x, a.z));
        sub_0047F760(poly, sub_004205A0(tmp, b.x, b.z));
        sub_0047F760(poly, sub_004205A0(tmp, c.x, c.z));
        if (polys.begin && polys.end - polys.begin < polys.cap - polys.begin)
            *polys.end++ = poly;
        else
            sub_00487860(&polys, polys.end, 1, &poly);
    }

    res = sub_004CFE10(this, this + 0x58, &polys);
    head = *(char ***)(res + 4);
    *count = *(int *)(res + 8) * 3;
    {
        unsigned long long sz = (unsigned long long)(unsigned)(*(int *)(res + 8) * 3) * 0x14;
        *out = sub_005E3B10((sz >> 32) ? 0xffffffffu : (unsigned)sz);
    }
    for (node = (char **)*head, j = 0; node != (char **)head; node = (char **)*node, j += 3) {
        void *poly = node[2];
        int k;
        for (k = 0; k < sub_004D3E80(poly); sub_0047F730(poly, 0), k++) {
            unsigned n = 0;
            unsigned short *t;
            float o[3], uv[2], r[4], d, *dst;
            while (1) {
                float *pt;
                if (!polys.begin || n >= (unsigned)(polys.end - polys.begin))
                    goto next;
                pt = sub_0047F6E0(poly);
                if (sub_00480A30(pt, polys.begin[n], pt))
                    break;
                n++;
            }
            t = idx + n * 3;
            sub_004CFC30(o, verts[t[0]], verts[t[1]], verts[t[2]], sub_0047F6E0(poly));
            dst = (float *)((char *)*out + (j + k) * 0x14);
            dst[0] = (float)(o[0] + 0.0f);
            dst[1] = (float)(o[1] + 0.01);
            dst[2] = (float)(0.0f + o[2]);
            uv[0] = o[0];
            uv[1] = o[2];
            sub_005B80A4(r, uv, matrix);
            d = r[0] - *(float *)(this + 0x84);
            d = __builtin_fabsf(d);
            dst[3] = d / *(float *)(this + 0x8c);
            d = r[1] - *(float *)(this + 0x88);
            d = __builtin_fabsf(d);
            dst[4] = d / *(float *)(this + 0x90);
        next:;
        }
        if (poly) {
            sub_0047F690(poly);
            sub_005E3E9C(poly);
        }
    }

    if (polys.begin) {
        for (i = 0; i < (unsigned)(polys.end - polys.begin); i++)
            if (polys.begin[i]) {
                sub_0047F690(polys.begin[i]);
                sub_005E3E9C(polys.begin[i]);
            }
        sub_005E3E9C(polys.begin);
    }
}
