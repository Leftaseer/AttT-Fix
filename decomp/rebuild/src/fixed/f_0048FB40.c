/* 0x0048FB40: the intersection of two polygons (a, b) as a new 8-byte polygon (0x0043BBC0): b's vertices inside a and
 * a's inside b (0x00480A30, its EAX given the vertex), then the crossings of their edges (0x0047FE30, 0x00480410 type
 * 3, the point 0x0047F980), each added once (0x0048A700, 0x0047F760; the polygons' cursors advance by 0x0047F730).
 * Empty: freed (0x0047F690) and 0. Otherwise the lowest vertex is the pivot; the others' offsets from it (0x0047F400,
 * 0x0047F390) are collected in a vector (push_back inline: 0x004BA1F0 / 0x0050A740) and sorted (0x0048EC60), and the
 * polygon rebuilt from them (0x0047F7F0, 0x0047F370) with the pivot last; returns 0x00480B50 of it. The this pointer
 * is unused */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_48FB40;
typedef struct { unsigned int d[2]; } P8_48FB40;
DECOMP_C void *__thiscall sub_0043BBC0(void *self);
DECOMP_C V2_48FB40 *__thiscall sub_004205A0(V2_48FB40 *self, float x, float y);
DECOMP_C int __thiscall sub_004D3E80(void *poly);
DECOMP_C float *__thiscall sub_0047F6E0(void *poly);
DECOMP_C unsigned char __cdecl sub_00480A30(void *eax, void *poly, void *pt);
DECOMP_C P8_48FB40 *__thiscall sub_0048A0F0(P8_48FB40 *self, void *pt);
DECOMP_C unsigned char __stdcall sub_0048A700(void *poly, P8_48FB40 pt);
DECOMP_C void __thiscall sub_0047F760(void *self, void *pt);
DECOMP_C void *__thiscall sub_0047F730(void *poly, int which);
DECOMP_C void __thiscall sub_0047FE30(void *poly, void *edge);
DECOMP_C int __thiscall sub_00480410(void *self, void *other, float *t);
DECOMP_C float *__thiscall sub_0047F980(void *self, void *out, float t);
DECOMP_C void __thiscall sub_0047F690(void *self);
DECOMP_C void __thiscall sub_0048DC10(void *self, unsigned int n);
DECOMP_C unsigned char __thiscall sub_0047F400(void *self, void *pt);
DECOMP_C float *__thiscall sub_0047F390(void *self, void *out, void *pt);
DECOMP_C void __cdecl sub_004BA1F0(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);
DECOMP_C void __thiscall sub_0050A740(void *self, void *where, unsigned int n, void *val);
DECOMP_C void __cdecl sub_0048EC60(void *first, void *last, int n);
DECOMP_C void __thiscall sub_0047F7F0(void *self);
DECOMP_C void *__thiscall sub_0047F370(void *self, void *out, void *pt);
DECOMP_C void *__cdecl sub_00480B50(void *path);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void __cdecl sub_005E3E9C(void *p);

static void addif_48FB40(void *res, void *pt)
{
    P8_48FB40 v;
    sub_0048A0F0(&v, pt);
    if (!sub_0048A700(res, v))
        sub_0047F760(res, pt);
}

static void inside_48FB40(void *res, void *outer, void *poly)
{
    int i;
    for (i = 0; i < sub_004D3E80(poly); i++) {
        float *v = sub_0047F6E0(poly);
        if (sub_00480A30(v, outer, v))
            addif_48FB40(res, sub_0047F6E0(poly));
        sub_0047F730(poly, 0);
    }
}

DECOMP(0048FB40)
void *__thiscall f_0048FB40(void *this, void *a, void *b)
{
    void *res = sub_005E3EAE(8);
    V2_48FB40 p;
    struct { unsigned int alloc; V2_48FB40 *begin, *end, *cap; } vec;
    unsigned int typ = 0, cnt;
    int i, j;
    res = res ? sub_0043BBC0(res) : 0;
    sub_004205A0(&p, 0.0f, 0.0f);
    inside_48FB40(res, a, b);
    inside_48FB40(res, b, a);
    for (i = 0; i < sub_004D3E80(b); i++) {
        unsigned int eb[4];
        sub_0047FE30(b, eb);
        for (j = 0; j < sub_004D3E80(a); j++) {
            unsigned int ea[4];
            float t, pt[2];
            sub_0047FE30(a, ea);
            typ = (unsigned int)sub_00480410(ea, eb, &t);
            sub_0047F980(ea, pt, t);
            if (typ == 3)
                addif_48FB40(res, pt);
            sub_0047F730(a, 0);
        }
        sub_0047F730(b, 0);
    }
    if (!sub_004D3E80(res)) {
        if (res) {
            sub_0047F690(res);
            sub_005E3E9C(res);
        }
        return 0;
    }
    p = *(V2_48FB40 *)sub_0047F6E0(res);
    sub_0047F730(res, 0);
    for (i = 1; i < sub_004D3E80(res); i++) {
        double py = p.y;
        if (py > sub_0047F6E0(res)[1])
            p = *(V2_48FB40 *)sub_0047F6E0(res);
        sub_0047F730(res, 0);
    }
    vec.begin = vec.end = vec.cap = 0;
    sub_0048DC10(&vec, sub_004D3E80(res));
    for (i = 0; i < sub_004D3E80(res); i++) {
        if (sub_0047F400(sub_0047F6E0(res), &p)) {
            float d[2], *r = sub_0047F390(sub_0047F6E0(res), d, &p);
            V2_48FB40 val;
            val.x = r[0];
            val.y = r[1];
            if (vec.begin && (unsigned int)(vec.end - vec.begin) < (unsigned int)(vec.cap - vec.begin)) {
                unsigned int x = typ & 0xffffff00;
                sub_004BA1F0(&val, vec.end, 1, &val, (unsigned int)(size_t)&vec, (void *)(size_t)x, x);
                vec.end++;
            } else
                sub_0050A740(&vec, vec.end, 1, &val);
        }
        sub_0047F730(res, 0);
    }
    sub_0047F730(res, 0);
    cnt = (unsigned int)(vec.end - vec.begin);
    sub_0048EC60(vec.begin, vec.end, cnt);
    for (i = 0; vec.begin && (unsigned int)i < cnt; i++) {
        V2_48FB40 q;
        P8_48FB40 w;
        unsigned int out[2];
        sub_0047F7F0(res);
        sub_004205A0(&q, vec.begin[i].x, vec.begin[i].y);
        sub_0047F760(res, sub_0047F370(sub_0048A0F0(&w, &q), out, &p));
        sub_0047F730(res, 0);
    }
    sub_0047F7F0(res);
    sub_0047F760(res, &p);
    sub_0047F730(res, 0);
    res = sub_00480B50(res);
    if (vec.begin)
        sub_005E3E9C(vec.begin);
    return res;
}
