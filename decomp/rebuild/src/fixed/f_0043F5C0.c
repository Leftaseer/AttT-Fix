/* 0x0043F5C0: whether the point (x, y) touches the polygon's outline: for each edge (0x0047FE30, then the next
 * vertex: 0x0047F730) its distance (0x0047FBC0) under eps, or 0x0043F2F0 (the edge test with a step of 2 * eps
 * truncated, from the point as 0x0048A0F0 copies it, two zero vectors and the polygon); a bool in AL */
/* @conv - 0 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_43F5C0;
typedef struct { unsigned int d[2]; } P8_43F5C0;
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C void __thiscall sub_0047FE30(void *poly, void *edge);
DECOMP_C double __thiscall sub_0047FBC0(void *pt, void *edge);
DECOMP_C void __thiscall sub_0048A0F0(P8_43F5C0 *self, void *pt);
DECOMP_C V2_43F5C0 *__thiscall sub_004205A0(V2_43F5C0 *self, float x, float y);
DECOMP_C int __cdecl sub_0043F2F0(V2_43F5C0 *b, V2_43F5C0 *a, void *poly, P8_43F5C0 pt, int step);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);

DECOMP(0043F5C0)
unsigned char __cdecl f_0043F5C0(void *poly, float x, float y, float eps)
{
    void *pt = (char *)__builtin_frame_address(0) + 12;          /* (x, y) where they came */
    int n = sub_004D3E80(poly), i;
    for (i = 0; i < n; i++) {
        unsigned int edge[4];
        V2_43F5C0 a, b;
        P8_43F5C0 p;
        int step;
        float d;
        sub_0047FE30(poly, edge);
        d = (float)__builtin_fabs(sub_0047FBC0(pt, edge));
        if (eps > d)
            return 1;
        step = (int)eps * 2;
        sub_0048A0F0(&p, pt);
        if (sub_0043F2F0(sub_004205A0(&b, 0.0f, 0.0f), sub_004205A0(&a, 0.0f, 0.0f), poly, p, step))
            return 1;
        sub_0047F730(poly, 0);
    }
    return 0;
}
