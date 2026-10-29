/* 0x004CFE10: clips 2D polygons against an outline: for each polygon of the vector (0x004B6450 items) a new polygon
 * collects its points inside the outline, the outline's points inside it and the crossings of their edges
 * (0x00480410 kind 3, 0x0047F980), each only once (0x0048A700); empty results are freed; otherwise the points are
 * sorted by angle around the lowest one (0x0047F400, 0x0047F390, 0x0048EC60, 0x0047F370), the polygon rebuilt from
 * them, triangulated (0x00480B50) and the triangles spliced into the result list (new, 0x0C bytes), which is returned */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int d[2]; } P8_4CFE10;
typedef struct { void *alloc; P8_4CFE10 *begin, *end, *cap; } Vec_4CFE10;
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void __cdecl sub_005E3E9C(void *p);                                   /* operator delete */
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C unsigned int __thiscall sub_004B6450(void *self);
DECOMP_C void *__thiscall sub_0043BBC0(void *self);
DECOMP_C float *__thiscall sub_004205A0(void *self, float x, float y);
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C float *__thiscall sub_0047F6E0(void *poly);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);
DECOMP_C unsigned char __cdecl sub_00480A30(void *eax, void *poly, void *pt);
DECOMP_C void __thiscall sub_0048A0F0(P8_4CFE10 *self, void *pt);
DECOMP_C unsigned char __stdcall sub_0048A700(void *poly, P8_4CFE10 pt);
DECOMP_C void __thiscall sub_0047F760(void *self, void *pt);
DECOMP_C void __thiscall sub_0047FE30(void *poly, void *edge);
DECOMP_C int __thiscall sub_00480410(void *self, void *other, float *t);
DECOMP_C float *__thiscall sub_0047F980(void *self, void *out, float t);
DECOMP_C void __thiscall sub_0047F690(void *self);
DECOMP_C unsigned char __thiscall sub_0047F400(void *self, void *pt);
DECOMP_C float *__thiscall sub_0047F390(void *self, void *out, void *pt);
DECOMP_C void __cdecl sub_004BA1F0(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);
DECOMP_C void __thiscall sub_0050A740(void *self, void *where, unsigned int n, void *val);
DECOMP_C void __cdecl sub_0048EC60(void *first, void *last, int n);
DECOMP_C void __thiscall sub_0047F7F0(void *self);
DECOMP_C void *__thiscall sub_0047F370(void *self, void *out, void *pt);
DECOMP_C void **__cdecl sub_00480B50(void *path);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);

/* adds pt to res unless it is there already */
static void add_4CFE10(void *res, void *pt)
{
    P8_4CFE10 c;
    sub_0048A0F0(&c, pt);
    if (!sub_0048A700(res, c))
        sub_0047F760(res, pt);
}

DECOMP(004CFE10)
void *__thiscall f_004CFE10(void *this, void *outline, void *polys)
{
    void **mem = sub_005E3EAE(0xc), **R = 0;
    unsigned int i;

    if (mem) {
        mem[1] = sub_004C2F40();
        mem[2] = 0;
        R = mem;
    }
    for (i = 0; i < sub_004B6450(polys); i++) {
        void *tri = (*(void ***)((char *)polys + 4))[i];
        void *m = sub_005E3EAE(8), *P = 0;
        float low[2];
        int k, a;
        if (m)
            P = sub_0043BBC0(m);
        sub_004205A0(low, 0.0f, 0.0f);

        for (k = 0; k < sub_004D3E80(tri); sub_0047F730(tri, 0), k++) {
            float *pt = sub_0047F6E0(tri);
            if (sub_00480A30(pt, outline, pt))
                add_4CFE10(P, sub_0047F6E0(tri));
        }
        for (k = 0; k < sub_004D3E80(outline); sub_0047F730(outline, 0), k++) {
            float *pt = sub_0047F6E0(outline);
            if (sub_00480A30(pt, tri, pt))
                add_4CFE10(P, sub_0047F6E0(outline));
        }
        for (a = 0; a < sub_004D3E80(tri); sub_0047F730(tri, 0), a++) {
            unsigned int ea[8];
            sub_0047FE30(tri, ea);
            for (k = 0; k < sub_004D3E80(outline); sub_0047F730(outline, 0), k++) {
                unsigned int eb[8];
                float t, x[2];
                int r;
                sub_0047FE30(outline, eb);
                r = sub_00480410(eb, ea, &t);
                sub_0047F980(eb, x, t);
                if (r == 3)
                    add_4CFE10(P, x);
            }
        }

        if (sub_004D3E80(P) == 0) {
            if (P) {
                sub_0047F690(P);
                sub_005E3E9C(P);
            }
        } else {
            Vec_4CFE10 v;
            unsigned int cnt, j;
            void **L, **head;
            float *pt = sub_0047F6E0(P);
            low[0] = pt[0];
            low[1] = pt[1];
            sub_0047F730(P, 0);
            for (k = 1; k < sub_004D3E80(P); sub_0047F730(P, 0), k++)
                if (low[1] > sub_0047F6E0(P)[1]) {
                    pt = sub_0047F6E0(P);
                    low[0] = pt[0];
                    low[1] = pt[1];
                }
            v.begin = v.end = v.cap = 0;
            for (k = 0; k < sub_004D3E80(P); sub_0047F730(P, 0), k++)
                if (sub_0047F400(sub_0047F6E0(P), low)) {
                    float d[2], *r = sub_0047F390(sub_0047F6E0(P), d, low);
                    P8_4CFE10 val;
                    ((float *)&val)[0] = r[0];
                    ((float *)&val)[1] = r[1];
                    if (v.begin && (unsigned int)(v.end - v.begin) < (unsigned int)(v.cap - v.begin)) {
                        unsigned int x = (unsigned int)(size_t)mem & 0xffffff00;
                        sub_004BA1F0(&val, v.end, 1, &val, (unsigned int)(size_t)&v, (void *)(size_t)x, x);
                        v.end++;
                    } else
                        sub_0050A740(&v, v.end, 1, &val);
                }
            sub_0047F730(P, 0);
            cnt = (unsigned int)(v.end - v.begin);
            sub_0048EC60(v.begin, v.end, cnt);
            for (j = 0; v.begin && j < cnt; j++) {
                float tv[2], o[2];
                P8_4CFE10 c;
                sub_0047F7F0(P);
                sub_004205A0(tv, ((float *)&v.begin[j])[0], ((float *)&v.begin[j])[1]);
                sub_0048A0F0(&c, tv);
                sub_0047F760(P, sub_0047F370(&c, o, low));
                sub_0047F730(P, 0);
            }
            sub_0047F7F0(P);
            sub_0047F760(P, low);
            sub_0047F730(P, 0);

            L = sub_00480B50(P);
            head = (void **)R[1];
            if (R != L && (cnt = (unsigned int)(size_t)L[2]) != 0) {
                void **lh = (void **)L[1], **first = (void **)lh[0], **t;
                sub_004E0EF0(R, cnt);
                L[2] = (void *)((size_t)L[2] - cnt);
                *(void ***)first[1] = lh;
                *(void ***)lh[1] = head;
                *(void ***)head[1] = first;
                t = (void **)head[1];
                head[1] = lh[1];
                lh[1] = first[1];
                first[1] = t;
            }
            if (L) {
                void **lh = (void **)L[1], **n = (void **)lh[0];
                lh[0] = lh;
                ((void **)L[1])[1] = L[1];
                L[2] = 0;
                while (n != (void **)L[1]) {
                    void **nx = (void **)n[0];
                    sub_005E3E9C(n);
                    n = nx;
                }
                sub_005E3E9C(L[1]);
                L[1] = 0;
                sub_005E3E9C(L);
            }
            if (v.begin)
                sub_005E3E9C(v.begin);
        }
    }
    return R;
}
