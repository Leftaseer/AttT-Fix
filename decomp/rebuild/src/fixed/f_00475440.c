/* 0x00475440: MatrixMeshSubObject loading from a reader (arg; 0x00458F80 reads): a count passed to the reader's
 * progress (+0x24 vf0C); the vertices (+0x18 of them, 32 bytes, FVF 0x112) read into a new managed vertex buffer
 * (+0x1C) and the 16-bit indices into an index buffer (+0x20; +0x14 triangles), failures to 0x00458940
 * (".\MatrixMeshSubObject.cpp"); the parts (+0x04 vector of 0x6C bytes, sized by 0x00475330 with a part whose only
 * initialised member is its name, by value): each reads 0x44 bytes, its texture's name (+0x44, up to 256 bytes) and
 * first index (+0x64), and loads the texture (+0x60, a new 0x54-byte 0x004DF920); each part's triangle count (+0x68)
 * runs to the next part's first index (the last's to the end); finally +0x78 is read */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[0x6c / 4]; } Part_475440;
DECOMP_C void __thiscall sub_00458F80(void *self, void *dst, unsigned int n);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void __thiscall sub_00475330(void *self, unsigned int n, Part_475440 proto);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *file, int a);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__cdecl sub_005E40BE(void *p, int c, unsigned int n);   /* memset */
DECOMP_C char d_006C8C10[], d_0060E9E8[];
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *prog_475440)(void *self, unsigned int n);
typedef long (__stdcall *create_475440)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_475440)(void *self, unsigned int off, unsigned int size, void **data, unsigned int fl);
typedef long (__stdcall *com_475440)(void *self);

#define DEV (*(void ***)d_006C8C10)

DECOMP(00475440)
void __thiscall f_00475440(void *this, char *rd)
{
    char *s = (char *)this, *e;
    unsigned int n, len, i;
    void *data, **b, *m;
    char name[0x100];
    sub_00458F80(rd, &n, 4);
    b = *(void ***)(rd + 0x24);
    ((prog_475440)(*(void ***)b)[0xc / 4])(b, n);
    sub_00458F80(rd, &n, 4);
    sub_00458940(((create_475440)(*(void ***)DEV)[0x68 / 4])(DEV, n << 5, 8, 0x112, 1, s + 0x1c, 0), d_0060E9E8, 0x44);
    b = *(void ***)(s + 0x1c);
    ((lock_475440)(*(void ***)b)[0x2c / 4])(b, 0, 0, &data, 0);
    sub_00458F80(rd, data, n << 5);
    b = *(void ***)(s + 0x1c);
    ((com_475440)(*(void ***)b)[0x30 / 4])(b);
    *(unsigned int *)(s + 0x18) = n;
    sub_00458F80(rd, &n, 4);
    sub_00458940(((create_475440)(*(void ***)DEV)[0x6c / 4])(DEV, n * 2, 8, 0x65, 1, s + 0x20, 0), d_0060E9E8, 0x59);
    b = *(void ***)(s + 0x20);
    ((lock_475440)(*(void ***)b)[0x2c / 4])(b, 0, 0, &data, 0);
    sub_00458F80(rd, data, n * 2);
    b = *(void ***)(s + 0x20);
    ((com_475440)(*(void ***)b)[0x30 / 4])(b);
    *(unsigned int *)(s + 0x14) = n / 3;
    sub_00458F80(rd, &n, 4);
    {
        Part_475440 proto;
        __builtin_memset(&proto, 0, sizeof proto);
        imp_006071E0((char *)&proto + 0x44);
        sub_00475330(s + 4, n, proto);
    }
    for (i = 0; i < n; i++) {
        e = *(char **)(s + 8) + i * 0x6c;
        sub_00458F80(rd, e, 0x44);
        sub_005E40BE(name, 0, 0x100);
        sub_00458F80(rd, &len, 4);
        sub_00458F80(rd, name, len);
        imp_006072F8(*(char **)(s + 8) + i * 0x6c + 0x44, name);
        sub_00458F80(rd, *(char **)(s + 8) + i * 0x6c + 0x64, 2);
        m = sub_005E3EAE(0x54);
        if (m)
            m = sub_004DF920(m, *(char **)(s + 8) + i * 0x6c + 0x44, 0);
        *(void **)(*(char **)(s + 8) + i * 0x6c + 0x60) = m;
    }
    for (i = 0;; i++) {
        char *v = *(char **)(s + 8);
        unsigned int cnt = v ? (unsigned int)((int)(*(char **)(s + 0xc) - v) / 0x6c) : 0;
        if (i >= cnt - 1)
            break;
        e = v + i * 0x6c;
        *(int *)(e + 0x68) = ((int)*(unsigned short *)(e + 0xd0) - (int)*(unsigned short *)(e + 0x64)) / 3;
    }
    e = *(char **)(s + 0xc);
    *(int *)(e - 4) = *(int *)(s + 0x14) - (int)*(unsigned short *)(e - 8) / 3;
    sub_00458F80(rd, s + 0x78, 4);
}
