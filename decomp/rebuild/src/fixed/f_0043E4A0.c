/* 0x0043E4A0: joins overlapping regions: the shown (+0x20) objects of the +0x9C list whose type (0x0043F710) is none
 * of 0..3 are gathered; for each one A at (x, z) (0x0043F7E0) the first other B not taken yet that lies within
 * 0x0060A208 on both axes, not below and behind it by 0x0060A200 on both, and whose polygon's (+0x0C) vertices all
 * fall inside A's polygon (0x0043F2F0 PointInPolygon with A at its place and B at its; each tested vertex is removed,
 * 0x0047F730) is taken: B is handed to 0x0043E3E0 afterwards and A goes on to the next */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_43E4A0;
typedef struct { unsigned int d[2]; } P8_43E4A0;
typedef struct { unsigned int alloc; char **head; unsigned int size; } List_43E4A0;
DECOMP_C int __thiscall sub_0043F710(void *self);
DECOMP_C void __thiscall sub_005A3680(void *self, void *val);
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C V2_43E4A0 *__thiscall sub_004205A0(V2_43E4A0 *self, float x, float y);
DECOMP_C float *__thiscall sub_0043F7E0(void *self, float *out);
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C void *__thiscall sub_0047F6E0(void *poly);
DECOMP_C void __thiscall sub_0048A0F0(P8_43E4A0 *self, void *pt);
DECOMP_C int __cdecl sub_0043F2F0(V2_43E4A0 *b, V2_43E4A0 *a, void *poly, P8_43E4A0 pt, int step);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void __thiscall sub_0043E3E0(void *self, void *obj);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_0060A208[], d_0060A200[];

static void push_43E4A0(List_43E4A0 *l, void *val)
{
    char **head = l->head, **nn = sub_005AD6C0(head, (char **)head[1], val);
    sub_004E0EF0(l, 1);
    head[1] = (char *)nn;
    *(char ***)nn[1] = nn;
}

static int has_43E4A0(List_43E4A0 *l, int v)
{
    char **n;
    for (n = (char **)l->head[0]; n != l->head; n = (char **)n[0])
        if ((int)(size_t)n[2] == v)
            return 1;
    return 0;
}

static void free_43E4A0(List_43E4A0 *l)
{
    char **head = l->head, **n = (char **)head[0], **next;
    head[0] = (char *)head;
    head[1] = (char *)head;
    for (; n != head; n = next) {
        next = (char **)n[0];
        sub_005E3E9C(n);
    }
    sub_005E3E9C(head);
}

static V2_43E4A0 at_43E4A0(void *o)
{
    float a[3], b[3], *p, *q;
    V2_43E4A0 t;
    p = sub_0043F7E0(o, a);
    q = sub_0043F7E0(o, b);
    return *sub_004205A0(&t, p[0], q[2]);
}

DECOMP(0043E4A0)
void __thiscall f_0043E4A0(void *this)
{
    char *s = (char *)this, **head, **nd;
    struct { unsigned int alloc; void **begin, **end, **cap; } v;
    List_43E4A0 taken, idx;
    V2_43E4A0 pa, pb;
    int n, i, j;
    v.begin = v.end = v.cap = 0;
    taken.head = (char **)sub_004C2F40();
    taken.size = 0;
    idx.head = (char **)sub_004C2F40();
    idx.size = 0;
    head = *(char ***)(s + 0x9c);
    for (nd = (char **)head[0]; nd != head; nd = (char **)nd[0]) {
        char *o = nd[2];
        if (o[0x20] && sub_0043F710(o) && sub_0043F710(o) != 1 && sub_0043F710(o) && sub_0043F710(o) != 3 &&
            sub_0043F710(o) != 2)
            sub_005A3680(&v, &o);
    }
    sub_004205A0(&pa, 0.0f, 0.0f);
    sub_004205A0(&pb, 0.0f, 0.0f);
    n = v.begin ? (int)(v.end - v.begin) : 0;
    for (i = 0; i < n; i++) {
        char *a = (char *)v.begin[i];
        pa = at_43E4A0(a);
        for (j = 0; j < n; j++) {
            char *b;
            void *poly, *apoly;
            float dx, dz;
            int k;
            if (has_43E4A0(&idx, j) || i == j)
                continue;
            b = (char *)v.begin[j];
            pb = at_43E4A0(b);
            dx = pa.x - pb.x;
            if (__builtin_fabsf(dx) > *(double *)d_0060A208)
                continue;
            dz = pa.y - pb.y;
            if (__builtin_fabsf(dz) > *(double *)d_0060A208)
                continue;
            if (*(double *)d_0060A200 > dx && *(double *)d_0060A200 > dz)
                continue;
            poly = *(void **)(b + 0xc);
            apoly = *(void **)(a + 0xc);
            if (sub_004D3E80(poly) - 1 <= 0)
                continue;
            for (k = 0; k < sub_004D3E80(poly) - 1; k++) {
                P8_43E4A0 pt;
                sub_0048A0F0(&pt, sub_0047F6E0(poly));
                if (sub_0043F2F0(&pa, &pb, apoly, pt, 0) != 1)
                    break;
                sub_0047F730(poly, 0);
            }
            if (k < sub_004D3E80(poly) - 1)
                continue;
            if (!has_43E4A0(&idx, j)) {
                push_43E4A0(&taken, &b);
                push_43E4A0(&idx, &j);
            }
            break;
        }
    }
    for (nd = (char **)taken.head[0]; nd != taken.head; nd = (char **)nd[0])
        sub_0043E3E0(this, nd[2]);
    free_43E4A0(&idx);
    free_43E4A0(&taken);
    if (v.begin)
        sub_005E3E9C(v.begin);
}
