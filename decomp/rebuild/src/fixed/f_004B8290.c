/* 0x004B8290: an object grid's setup (default size, level name by value): with a name the script's ObjectCells entry
 * for it (0x004B65E0 with a nil default) gives the size (its "Size", 0x0057AD40 truncated) and the squared "Distance"
 * (+0x98), else (no name or no entry) the default is the size (+0x84); the rows (+0x74 vector, 0x004CE6B0) each get
 * size cells of 0x88 bytes (0x004B7BD0 with a cell whose hash set at +0x60 is built by 0x004CD110, the rest left as
 * it is); the cells split the terrain's box (0x00433620: x +0x18..+0x1C, z +0x20..+0x24) evenly: origin +0x88 / +0x8C,
 * step +0x90 / +0x94, each cell's corners (x, 0, z) at +0x00 and +0x54. Destroys its by-value name */
/* @conv ECX 32 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_4B8290;                  /* nScript::Table */
typedef struct { unsigned int w[4]; } Vec_4B8290;                  /* std::vector */
typedef struct { unsigned int w[0x88 / 4]; } Cell_4B8290;
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_004B65E0(void *self, Tbl_4B8290 *out, const void *key, const Tbl_4B8290 *def);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_004CE6B0(void *self, unsigned int n, Vec_4B8290 val);
DECOMP_C void __thiscall sub_004CD110(void *self, const void *a, const void *b);
DECOMP_C void __thiscall sub_004B7BD0(void *self, unsigned int n, Cell_4B8290 val);
DECOMP_C char *__cdecl sub_00433620(void);
DECOMP_C char d_00607CC4[], d_006110C8[], d_006110C0[], d_006110B4[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(004B8290)
void __thiscall f_004B8290(void *this, unsigned int n, unsigned int w0, unsigned int w1, unsigned int w2,
                           unsigned int w3, unsigned int w4, unsigned int size, unsigned int w6)
{
    char *s = (char *)this, *g, *row;
    void *name = (char *)__builtin_frame_address(0) + 0xc;
    unsigned int i, j;
    float a, b, c, d, nf;
    if (!size)
        *(unsigned int *)(s + 0x84) = n;
    else {
        Tbl_4B8290 def, t, e;
        def.w[1] = 0;
        def.w[0] = (unsigned int)d_00607CC4;
        def.w[2] = 0xffffffff;
        sub_004B65E0(sub_004323E0(&t, d_006110C8), &e, name, &def);
        sub_004220A0(&t);
        sub_004220A0(&def);
        if ((int)e.w[2] > 0) {
            float dist;
            *(unsigned int *)(s + 0x84) = (unsigned int)(long long)sub_0057AD40(&e, d_006110C0);
            dist = sub_0057AD40(&e, d_006110B4);
            *(float *)(s + 0x98) = dist * dist;
        } else
            *(unsigned int *)(s + 0x84) = n;
        sub_004220A0(&e);
    }
    {
        Vec_4B8290 v;
        v.w[1] = 0;
        v.w[2] = 0;
        v.w[3] = 0;
        sub_004CE6B0(s + 0x74, *(unsigned int *)(s + 0x84), v);
    }
    for (i = 0; (int)i < *(int *)(s + 0x84); i++) {
        Cell_4B8290 cell;
        unsigned int cnt = *(unsigned int *)(s + 0x84);
        row = *(char **)(s + 0x78) + i * 0x10;
        sub_004CD110((char *)&cell + 0x60, &n, &n);
        sub_004B7BD0(row, cnt, cell);
    }
    g = sub_00433620();
    a = *(float *)(g + 0x1c);
    b = *(float *)(g + 0x18);
    nf = (float)*(int *)(s + 0x84);
    *(float *)(s + 0x90) = (a - b) / nf;
    c = *(float *)(g + 0x24);
    d = *(float *)(g + 0x20);
    *(float *)(s + 0x94) = (c - d) / nf;
    *(float *)(s + 0x88) = *(float *)(g + 0x18);
    *(float *)(s + 0x8c) = *(float *)(g + 0x20);
    for (i = 0; (int)i < *(int *)(s + 0x84); i++) {
        float fi = (float)(int)i, fi1 = (float)(int)(i + 1);
        for (j = 0; (int)j < *(int *)(s + 0x84); j++) {
            float sx = *(float *)(s + 0x90), ox = *(float *)(s + 0x88), sz, oz;
            float *cl = (float *)(*(char **)(*(char **)(s + 0x78) + i * 0x10 + 4) + j * 0x88);
            float x0 = fi * sx + ox, z0;
            sz = *(float *)(s + 0x94);
            oz = *(float *)(s + 0x8c);
            z0 = (float)(int)j * sz + oz;
            cl[0] = x0;
            cl[1] = 0.0f;
            cl[2] = z0;
            cl = (float *)(*(char **)(*(char **)(s + 0x78) + i * 0x10 + 4) + j * 0x88 + 0x54);
            cl[0] = sx * fi1 + ox;
            cl[1] = 0.0f;
            cl[2] = sz * (float)(int)(j + 1) + oz;
        }
    }
    imp_00607330(name);
}
