/* 0x00491160: CQuadTree::CQuadTree(&vb, &ib, &decl, file, name, depth, a7, a8, a9, a10): empty node vectors; depth
 * (+0x58) gives 4^depth nodes (+0x64) and 2^depth patches per side (+0x68); the patch rows (+0x19C, +0x1AC) get
 * that many zeroed columns, the patches (+4, 0x14 bytes) are sized (0x00490E40, 0x00490530); the node buffers
 * (+0x190 of 12 bytes, +0x184) are made; the file is loaded (0x0048C240) and the vertex buffer (+0x16C), declaration
 * (+0x14C) and a new 16-bit index buffer (+0x168, +0x178 indices) are handed out; the bounds (+0x9C..+0xBC) give the
 * patch size (+0x5C / +0x60) and the root (0x0048C2D0, size 0x50; +0x1BC); the camera is +0x164; outside the three
 * continent reflection trees a reflection holder (0x00435CF0, +0x17C) gets the name (0x00453340) */
/* @conv ECX 88 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_491160;                 /* std::string */
typedef struct { void *alloc; unsigned int *begin, *end, *cap; } Vec_491160;
typedef struct { unsigned int w[5]; } Pat_491160;
typedef struct { float x0, y0, x1, y1; } Rect_491160;
DECOMP_C void *__cdecl sub_00435CF0(void);
DECOMP_C double decomp_CIpow(double x, double y);
DECOMP_C void __thiscall sub_004909E0(void *self, unsigned int n, Vec_491160 val);
DECOMP_C void __thiscall sub_00487860(void *self, void *where, unsigned int n, void *val);
DECOMP_C void __thiscall sub_00490E40(void *self, unsigned int n, Pat_491160 val);
DECOMP_C void __thiscall sub_00490530(void *self, unsigned int n, int a);
DECOMP_C void __cdecl sub_005E3EBA(void *p);                                   /* operator delete[] */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                        /* operator new[] */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                        /* operator new */
DECOMP_C void __thiscall sub_0048C240(void *self, Str_491160 file);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__thiscall sub_0048C2D0(void *self, int depth, unsigned int a, Rect_491160 r);
DECOMP_C void *__cdecl sub_00424E70(void);
DECOMP_C void __thiscall sub_00453340(void *self, void *name);
DECOMP_C char d_0060FE3C[], d_0060BD00[], d_0060FEA0[], d_0060FE7C[], d_0060FE58[], d_00609B68[], d_0060A308[],
    d_006C8C10[], d_0060FEC4[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef long (__stdcall *cib_491160)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                     unsigned int pool, void **ib, void *share);

static int own_491160(void *name)
{
    return imp_00607214(name, d_0060FEA0) && imp_00607214(name, d_0060FE7C) && imp_00607214(name, d_0060FE58);
}

/* every row of the vector of vectors at rows gets n zeroed columns */
static void cols_491160(char *this, char *rows)
{
    unsigned int i;
    for (i = 0; *(Vec_491160 **)(rows + 4) &&
                i < (unsigned int)(*(Vec_491160 **)(rows + 8) - *(Vec_491160 **)(rows + 4)); i++) {
        Vec_491160 *e = *(Vec_491160 **)(rows + 4) + i;
        unsigned int want = *(unsigned int *)(this + 0x68), zero = 0;
        unsigned int size = e->begin ? (unsigned int)(e->end - e->begin) : 0;
        if (size < want)
            sub_00487860(e, e->end, want - size, &zero);
        else if (e->begin && want < (unsigned int)(e->end - e->begin) && e->begin + want != e->end)
            e->end = e->begin + want;
    }
}

static unsigned int level_491160(double base, unsigned char depth)
{
    float f = (float)decomp_CIpow(base, (float)depth);
    return (unsigned int)(long long)f;
}

DECOMP(00491160)
void *__thiscall f_00491160(char *this, void **vb, void **ib, void **decl, unsigned int f0, unsigned int f1,
                            unsigned int f2, unsigned int f3, unsigned int f4, unsigned int f5, unsigned int f6,
                            unsigned int n0, unsigned int n1, unsigned int n2, unsigned int n3, unsigned int n4,
                            unsigned int n5, unsigned int n6, unsigned int depth, int a7, int a8, float a9,
                            unsigned int a10)
{
    /* the two strings passed by value, in place on the stack */
    Str_491160 *file = (Str_491160 *)((char *)__builtin_frame_address(0) + 8 + 4 * 3);
    Str_491160 *name = (Str_491160 *)((char *)__builtin_frame_address(0) + 8 + 4 * 10);
    Vec_491160 ev;
    Pat_491160 ep;
    Str_491160 fc;
    Rect_491160 r;
    unsigned int i, n;
    void *dev, *o;

    *(int *)(this + 4) = 0;
    *(int *)(this + 8) = 0;
    *(int *)(this + 0xc) = 0;
    *(int *)(this + 0x14) = 0;
    *(int *)(this + 0x18) = 0;
    *(int *)(this + 0x1c) = 0;
    *(int *)(this + 0x24) = 0;
    *(int *)(this + 0x28) = 0;
    *(int *)(this + 0x2c) = 0;
    *(int *)(this + 0x34) = 0;
    *(int *)(this + 0x38) = 0;
    *(int *)(this + 0x3c) = 0;
    this[0x58] = (char)depth;
    imp_00607334(this + 0x80, name);
    *(int *)(this + 0x144) = 0;
    *(int *)(this + 0x154) = a7;
    this[0x158] = (char)a8;
    *(float *)(this + 0x15c) = a9;
    *(void **)(this + 0x180) = d_0060FE3C;
    *(int *)(this + 0x184) = 0;
    *(int *)(this + 0x188) = 0;
    *(void **)(this + 0x18c) = d_0060BD00;
    *(int *)(this + 0x190) = 0;
    *(int *)(this + 0x194) = 0;
    *(int *)(this + 0x1a0) = 0;
    *(int *)(this + 0x1a4) = 0;
    *(int *)(this + 0x1a8) = 0;
    *(int *)(this + 0x1b0) = 0;
    *(int *)(this + 0x1b4) = 0;
    *(int *)(this + 0x1b8) = 0;
    if (own_491160(this + 0x80))
        *(void **)(this + 0x17c) = sub_00435CF0();

    *(unsigned int *)(this + 0x64) = level_491160(*(double *)d_00609B68, (unsigned char)this[0x58]);
    *(unsigned int *)(this + 0x68) = level_491160(*(double *)d_0060A308, (unsigned char)this[0x58]);
    ev.alloc = 0;
    ev.begin = ev.end = ev.cap = 0;
    sub_004909E0(this + 0x19c, *(unsigned int *)(this + 0x68), ev);
    cols_491160(this, this + 0x19c);
    ep.w[0] = 0;
    ep.w[1] = 0;
    ep.w[2] = 0;
    ep.w[3] = 0;
    ep.w[4] = 0;
    sub_00490E40(this, *(unsigned int *)(this + 0x68), ep);
    for (i = 0; *(Vec_491160 **)(this + 0x1a0) &&
                i < (unsigned int)(*(Vec_491160 **)(this + 0x1a4) - *(Vec_491160 **)(this + 0x1a0)); i++)
        sub_00490530(*(char **)(this + 4) + i * 0x14, *(unsigned int *)(this + 0x68), 0);
    sub_004909E0(this + 0x1ac, *(unsigned int *)(this + 0x68), ev);
    cols_491160(this, this + 0x1ac);

    n = *(unsigned int *)(this + 0x64);
    if (*(void **)(this + 0x190)) {
        sub_005E3EBA(*(void **)(this + 0x190));
        *(void **)(this + 0x190) = 0;
    }
    if (n) {
        unsigned long long sz = (unsigned long long)n * 12;
        *(void **)(this + 0x190) = sub_005E3B10((sz >> 32) ? 0xffffffffu : (unsigned int)sz);
    }
    *(int *)(this + 0x194) = 0;
    n = *(unsigned int *)(this + 0x64);
    if (*(void **)(this + 0x184)) {
        sub_005E3EBA(*(void **)(this + 0x184));
        *(void **)(this + 0x184) = 0;
    }
    if (n)
        *(void **)(this + 0x184) = sub_005E3B10(n);
    *(int *)(this + 0x188) = 0;
    for (i = 0; i < *(unsigned int *)(this + 0x64); i++)
        (*(int *)(this + 0x188))++;

    imp_00607334(&fc, file);
    sub_0048C240(this, fc);
    *decl = *(void **)(this + 0x14c);
    *vb = *(void **)(this + 0x16c);
    dev = *(void **)d_006C8C10;
    sub_00458940(((cib_491160)(*(void ***)dev)[0x6c / 4])(dev, *(unsigned int *)(this + 0x178) * 2, 8, 0x65, 1,
                                                          (void **)(this + 0x168), 0),
                 d_0060FEC4, 0x58);
    *ib = *(void **)(this + 0x168);

    {
        float a = *(float *)(this + 0x9c), b = *(float *)(this + 0xa8), c = *(float *)(this + 0xbc),
              d = *(float *)(this + 0xa4);
        long double cnt = (long double)*(unsigned int *)(this + 0x68);
        *(float *)(this + 0x70) = a;
        *(float *)(this + 0x74) = b;
        *(float *)(this + 0x7c) = c;
        *(float *)(this + 0x78) = d;
        *(float *)(this + 0x5c) = (float)(((long double)b - a) / cnt);
        *(float *)(this + 0x60) = (float)(((long double)d - c) / cnt);
    }
    o = sub_005E3EAE(0x50);
    if (o) {
        r.x0 = *(float *)(this + 0x70);
        r.y0 = *(float *)(this + 0x74);
        r.x1 = *(float *)(this + 0x78);
        r.y1 = *(float *)(this + 0x7c);
        o = sub_0048C2D0(o, (unsigned char)this[0x58], a10, r);
    }
    *(void **)(this + 0x1bc) = o;
    *(void **)(this + 0x164) = sub_00424E70();
    if (own_491160(this + 0x80))
        sub_00453340(*(void **)(this + 0x17c), this + 0x80);
    imp_00607330(file);
    imp_00607330(name);
    return this;
}
