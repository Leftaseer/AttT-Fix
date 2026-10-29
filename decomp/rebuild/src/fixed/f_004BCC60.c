/* 0x004BCC60: NSkinAnimation::CSkinMeshSubObject::Read (stream): reads the core (+0x18, 0x004BCAE0); room for all the
 * vertices of its four lists (+0x88 2-byte, +0x98 12-byte, +0xA8 20-byte, +0xB8 24-byte entries) at +0xD8
 * (0x00456870) which 0x004B9AA0 fills; for each of its +0x14 frames a vertex buffer of 32-byte vertices (write-only
 * dynamic, FVF 0x112) is created, filled by 0x004B9AA0 and appended to +0xEC (its current entry +0xF8 starting at the
 * first); the 16-bit indices (+0x38) go to a managed index buffer (+0xFC), a third of their count is the triangle
 * count (+0xE8); the 100-byte material records (+0xC8) become 0x6C-byte parts at +4 (0x00475330): their first 0x44
 * bytes, texture name (+0x44), first index (+0x60 -> +0x64) and texture (0x54 bytes, 0x004DF920 by name, +0x60), each
 * part's triangle count (+0x68) running to the next one's first index; the records are then cleared (0x004B9CF0 and
 * their names destroyed) and 0x006CA484's +4 grows to the most bones (+0x48, 24-byte entries) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[0x6c / 4]; } Part_4BCC60;
DECOMP_C void __thiscall sub_004BCAE0(void *self, void *stream);
DECOMP_C void __thiscall sub_00456870(void *self, unsigned int n);
DECOMP_C void __thiscall sub_004B9AA0(void *self, void *dst);
DECOMP_C void __cdecl sub_00458940(int hr, const char *file, int line);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void *__cdecl sub_005E4232(void *d, const void *s, unsigned int n);   /* memcpy */
DECOMP_C void __thiscall sub_00475330(void *self, unsigned int n, Part_4BCC60 proto);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *file, int a);
DECOMP_C char *__cdecl sub_004B9CF0(char *first, char *last, char *dest, unsigned int a, unsigned int b,
                                    unsigned int c);
DECOMP_C char d_006C8C10[], d_006111AC[], d_006CA484[];
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef int (__stdcall *create_4BCC60)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                       unsigned int pool, void **out, void *share);
typedef int (__stdcall *lock_4BCC60)(void *b, unsigned int off, unsigned int len, void **p, unsigned int flags);
typedef int (__stdcall *unlock_4BCC60)(void *b);

#define VT(o) (*(void ***)(o))
#define N(o, sz) (*(char **)(s + (o)) ? (int)((*(char **)(s + (o) + 4) - *(char **)(s + (o))) / (sz)) : 0)

DECOMP(004BCC60)
void __thiscall f_004BCC60(void *this, void *stream)
{
    char *s = (char *)this, *dev, **head, **nn, *e, *last;
    unsigned int total, k, i, n, cnt, off;
    void *p;
    sub_004BCAE0(s + 0x18, stream);
    total = N(0xb8, 24) + N(0xa8, 20) + N(0x98, 12) + N(0x88, 2);
    sub_00456870(s + 0xd8, total);
    sub_004B9AA0(this, *(void **)(s + 0xdc));
    for (k = 0; k < *(unsigned char *)(s + 0x14); k++) {
        void *vb;
        dev = *(char **)d_006C8C10;
        sub_00458940(((create_4BCC60)VT(dev)[0x68 / 4])(dev, total << 5, 0x208, 0x112, 0, &vb, 0), d_006111AC,
                     0x80);
        ((lock_4BCC60)VT(vb)[0x2c / 4])(vb, 0, 0, &p, 0);
        sub_004B9AA0(this, p);
        ((unlock_4BCC60)VT(vb)[0x30 / 4])(vb);
        head = *(char ***)(s + 0xf0);
        nn = sub_005AD6C0(head, (char **)head[1], &vb);
        sub_004E0EF0(s + 0xec, 1);
        head[1] = (char *)nn;
        *(char ***)nn[1] = nn;
        if (*(char ***)(s + 0xf8) == *(char ***)(s + 0xf0))
            *(char **)(s + 0xf8) = **(char ***)(s + 0xf0);
    }
    dev = *(char **)d_006C8C10;
    sub_00458940(((create_4BCC60)VT(dev)[0x6c / 4])(dev, N(0x38, 2) * 2, 8, 0x65, 1, (void **)(s + 0xfc), 0),
                 d_006111AC, 0x93);
    p = *(void **)(s + 0xfc);
    ((lock_4BCC60)VT(p)[0x2c / 4])(p, 0, 0, &p, 0);
    sub_005E4232(p, *(void **)(s + 0x38), N(0x38, 2) * 2);
    p = *(void **)(s + 0xfc);
    ((unlock_4BCC60)VT(p)[0x30 / 4])(p);
    *(unsigned int *)(s + 0xe8) = (unsigned int)N(0x38, 2) / 3;
    {
        Part_4BCC60 proto;
        imp_006071E0((char *)&proto + 0x44);
        sub_00475330(s + 4, N(0xc8, 100), proto);
    }
    for (i = 0, off = 0; *(char **)(s + 0xc8) && i < (unsigned int)N(0xc8, 100); i++, off += 100) {
        char *src = *(char **)(s + 0xc8) + off;
        void *o;
        e = *(char **)(s + 8) + i * 0x6c;
        __builtin_memcpy(e, src, 0x44);
        imp_0060731C(e + 0x44, *(char **)(s + 0xc8) + off + 0x44);
        *(unsigned short *)(*(char **)(s + 8) + i * 0x6c + 0x64) = *(unsigned short *)(*(char **)(s + 0xc8) + off + 0x60);
        o = sub_005E3EAE(0x54);
        o = o ? sub_004DF920(o, *(char **)(s + 8) + i * 0x6c + 0x44, 0) : 0;
        *(void **)(*(char **)(s + 8) + i * 0x6c + 0x60) = o;
    }
    cnt = i;
    for (k = 0; k < (unsigned int)(N(8, 0x6c) - 1); k++) {
        e = *(char **)(s + 8) + k * 0x6c;
        *(int *)(e + 0x68) = ((int)*(unsigned short *)(e + 0xd0) - (int)*(unsigned short *)(e + 0x64)) / 3;
    }
    last = *(char **)(s + 0xc);
    *(int *)(last - 4) = *(int *)(s + 0xe8) - (int)*(unsigned short *)(last - 8) / 3;
    if (*(char **)(s + 0xc8) != *(char **)(s + 0xcc)) {
        char *end = *(char **)(s + 0xcc), *ne, *q;
        unsigned int x = cnt & 0xffffff00;
        ne = sub_004B9CF0(end, end, *(char **)(s + 0xc8), x, x, x);
        for (q = ne; q != *(char **)(s + 0xcc); q += 100)
            imp_00607330(q + 0x44);
        *(char **)(s + 0xcc) = ne;
    }
    n = N(0x48, 24);
    if (n > *(unsigned int *)(*(char **)d_006CA484 + 4))
        *(unsigned int *)(*(char **)d_006CA484 + 4) = n;
}
