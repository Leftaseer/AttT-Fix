/* 0x0048B8D0: QuadTree loading from its file (+0x80, a reader 0x00459290 / 0x00458F80 / 0x00459010 / 0x00459170):
 * the tree (0x0048B700 into +0x9C), the vertex count (+0x14C) and its 32-byte vertices read straight into a new
 * managed vertex buffer (+0x16C, FVF 0x112; failures to 0x00458940, ".\QuadTree.cpp") and copied to +0x150; the
 * terrain (+0x17C) gets the vertices (0x004528F0) and later the indices (0x00452830) unless this is one of the three
 * "Continent<n>Reflection_QuadTree.dat"; each of the +0x158 parts (+0x154, names +0x15C) loads with its name by value,
 * the tree and the vertex range (vf0C); the window 0x006C889C is brought to the front, the buffer unlocked, and the
 * index count (+0x178) and 16-bit indices (+0x144) read. new[] sizes saturate on overflow as the compiler's do */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_48B8D0;                  /* std::string */
DECOMP_C void __thiscall sub_00459290(void *self, void *name, int a);
DECOMP_C void __thiscall sub_0048B700(void *self, void *rd, void *tree, int a);
DECOMP_C void __thiscall sub_00458F80(void *self, void *dst, unsigned int n);
DECOMP_C void __thiscall sub_004528F0(void *self, void *v, unsigned int n);
DECOMP_C void __thiscall sub_00452830(void *self, void *ix, unsigned int n);
DECOMP_C void __thiscall sub_00459010(void *self);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);
DECOMP_C void *__cdecl sub_005E4232(void *dst, const void *src, unsigned int n);      /* memcpy */
DECOMP_C char d_006C8C10[], d_0060FEC4[], d_0060FEA0[], d_0060FE7C[], d_0060FE58[], d_006C889C[];
DECOMP_C int (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C int (__stdcall *imp_00607658)(void *) __asm__("__imp__SetForegroundWindow@4");
typedef long (__stdcall *create_48B8D0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_48B8D0)(void *self, unsigned int off, unsigned int size, void **data, unsigned int fl);
typedef long (__stdcall *com_48B8D0)(void *self);
typedef void (__thiscall *part_48B8D0)(void *self, Str_48B8D0 name, void *tree, void *range);

#define DEV (*(void ***)d_006C8C10)

static unsigned int arr_48B8D0(unsigned int n, unsigned int size)
{
    unsigned long long t = (unsigned long long)n * size;
    return t >> 32 ? ~0u : (unsigned int)t;
}

static int plain_48B8D0(char *s)
{
    return (char)imp_00607214(s + 0x80, d_0060FEA0) && (char)imp_00607214(s + 0x80, d_0060FE7C) &&
           (char)imp_00607214(s + 0x80, d_0060FE58);
}

DECOMP(0048B8D0)
void __thiscall f_0048B8D0(void *this)
{
    char *s = (char *)this, *copy;
    unsigned int rd[0x30 / 4], n, nidx;
    struct { void *v; unsigned int n; } range;
    void *data, **vb;
    unsigned char i;
    sub_00459290(rd, s + 0x80, 1);
    *(int *)(s + 0x198) = 0;
    sub_0048B700(this, rd, s + 0x9c, 0);
    sub_00458F80(rd, s + 0x14c, 4);
    sub_00458940(((create_48B8D0)(*(void ***)DEV)[0x68 / 4])(DEV, *(unsigned int *)(s + 0x14c) << 5, 8, 0x112, 1,
                                                              s + 0x16c, 0),
                 d_0060FEC4, 0x47f);
    vb = *(void ***)(s + 0x16c);
    ((lock_48B8D0)(*(void ***)vb)[0x2c / 4])(vb, 0, 0, &data, 0);
    sub_00458F80(rd, data, *(unsigned int *)(s + 0x14c) << 5);
    if (plain_48B8D0(s))
        sub_004528F0(*(void **)(s + 0x17c), data, *(unsigned int *)(s + 0x14c));
    copy = sub_005E3B10(arr_48B8D0(*(unsigned int *)(s + 0x14c), 0x20));
    *(char **)(s + 0x150) = copy;
    sub_005E4232(copy, data, *(unsigned int *)(s + 0x14c) << 5);
    range.v = data;
    range.n = *(unsigned int *)(s + 0x14c);
    for (i = 0; i < (unsigned char)s[0x158]; i++) {
        Str_48B8D0 name;
        void **part;
        imp_00607334(&name, *(char **)(s + 0x15c) + i * 0x1c);
        part = (*(void ****)(s + 0x154))[i];
        ((part_48B8D0)(*(void ***)part)[0xc / 4])(part, name, s + 0x9c, &range);
    }
    imp_00607658(*(void **)d_006C889C);
    vb = *(void ***)(s + 0x16c);
    ((com_48B8D0)(*(void ***)vb)[0x30 / 4])(vb);
    sub_00458F80(rd, &nidx, 4);
    n = arr_48B8D0(nidx, 2);
    *(void **)(s + 0x144) = sub_005E3B10(n);
    sub_00458F80(rd, *(void **)(s + 0x144), nidx * 2);
    *(unsigned int *)(s + 0x178) = nidx;
    if (plain_48B8D0(s))
        sub_00452830(*(void **)(s + 0x17c), *(void **)(s + 0x144), *(unsigned int *)(s + 0x178));
    sub_00459010(rd);
    sub_00459170(rd);
}
