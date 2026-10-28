/* 0x00488A20: PolyLine::PolyLine(device, std::vector<D3DXVECTOR3> points by value, colour from, colour to): the 3D
 * render object base (0x004AD180 with an empty name), its vtable, FVF XYZ|DIFFUSE (+0x1C4); under two points throws
 * the std::string "PolyLine: Количество вершин должно быть не менее 2" (at least 2 vertices); a managed vertex buffer
 * (+0x1CC, from the device kept at +0x1D0) of a line list of 2 * (points - 1) vertices (+0x1C8), a failure reported
 * (0x00458940, ".\PolyLine.cpp") and thrown ("PolyLine: Ошибка создания буфера вершин", vertex buffer creation
 * failed); each segment from its start in the first colour to its end in the second; the "3dline" effect
 * (0x004AB810); frees the vector (callee-destroyed) and returns this. The vector arrives as its four dwords */
/* @conv ECX 28 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_0060FA8B[], d_0060F9BC[], d_0060F984[], d_0060F8EC[], d_0060F95C[], d_0060F954[], d_0069916C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef long (__stdcall *create_488A20)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_488A20)(void *self, unsigned int off, unsigned int size, unsigned int **data,
                                      unsigned int fl);
typedef long (__stdcall *com_488A20)(void *self);

static void throw_488A20(const char *text)
{
    unsigned int msg[7], thrown[7];         /* two std::string */
    imp_00607324(msg, text);
    imp_00607334(thrown, msg);
    sub_005E3EC0(thrown, d_0069916C);
}

DECOMP(00488A20)
void *__thiscall f_00488A20(void *this, void **dev, unsigned int v0, unsigned int *begin, unsigned int *end,
                            unsigned int cap, unsigned int c1, unsigned int c2)
{
    char *s = (char *)this;
    unsigned int name[7], n, i, *p, *q;
    long hr;
    void **vb;
    imp_00607324(name, d_0060FA8B);
    sub_004AD180(this, name, 0, 0);
    imp_00607330(name);
    *(void **)s = d_0060F9BC;
    *(unsigned int *)(s + 0x1c4) = 0x42;
    n = begin ? (unsigned int)((int)((char *)end - (char *)begin) / 12) : 0;
    if (!begin || n < 2)
        throw_488A20(d_0060F984);
    *(unsigned int *)(s + 0x1c8) = n * 2 - 2;
    *(void ***)(s + 0x1d0) = dev;
    hr = ((create_488A20)(*(void ***)dev)[0x68 / 4])(dev, (n * 2 - 2) << 4, 8, 0x42, 1, s + 0x1cc, 0);
    sub_00458940(hr, d_0060F8EC, 0x19);
    if (hr)
        throw_488A20(d_0060F95C);
    vb = *(void ***)(s + 0x1cc);
    ((lock_488A20)(*(void ***)vb)[0x2c / 4])(vb, 0, 0, &p, 0);
    for (i = 0, q = begin; i < n - 1; i++, q += 3) {
        p[0] = q[0], p[1] = q[1], p[2] = q[2], p[3] = c1;
        p[4] = q[3], p[5] = q[4], p[6] = q[5], p[7] = c2;
        p += 8;
    }
    vb = *(void ***)(s + 0x1cc);
    ((com_488A20)(*(void ***)vb)[0x30 / 4])(vb);
    imp_00607324(name, d_0060F954);
    sub_004AB810(this, name, 0);
    imp_00607330(name);
    sub_005E3E9C(begin);
    return this;
}
