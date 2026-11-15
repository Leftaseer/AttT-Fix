/* 0x00425B50: C3DLine's second constructor (six dwords and the shader value, ret 0x1C): the CRenderObject3D base with an
 * empty name (0x004AD180), vtable 0x00607DB4, z test on (+0x1CC = 1); the shared line effect is created on first use
 * (count 0x006C8710, 0x00448F10 named from 0x00607E84 into 0x006C870C) and counted.  The six values are gathered and
 * a 0x18-byte vertex buffer (FVF 2) is created through slot 0x68 of the device at 0x006C8C10; the result is checked
 * by 0x00458940 (line 0x48), the vertices go into the buffer through its lock slot 0x2C and unlock slot 0x30, and
 * the shader value lands at +0x1C8.  Returns this. */
/* @conv ECX 28 */
#include "auto_pre.h"
DECOMP_C char d_00607DB4[], d_0060FA8B[], d_00607E74[], d_00607E84[], d_006C8C10[];
DECOMP_C void *d_006C870C, *d_006C8714;
DECOMP_C unsigned int d_006C8710;
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__thiscall sub_00448F10(void *registry, void *name);
typedef long (__stdcall *create_425980)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_425980)(void *self, unsigned int off, unsigned int size, unsigned int **data,
                                      unsigned int flags);
typedef void (__stdcall *unlock_425980)(void *self);

#define DEV (*(void ***)d_006C8C10)

DECOMP(00425B50)
void *__thiscall f_00425B50(void *this, unsigned int a1, unsigned int a2, unsigned int a3,
                            unsigned int a4, unsigned int a5, unsigned int a6, unsigned int shader)
{
    char *s = (char *)this;
    unsigned int name[7], effect[7], verts[6], *data;
    void *vb;
    void **vt;
    long hr;

    imp_00607324(name, d_0060FA8B);
    sub_004AD180(s, name, 0, 0);
    imp_00607330(name);
    *(const void **)s = d_00607DB4;
    s[0x1cc] = 1;
    if (d_006C8710 == 0) {
        imp_00607324(effect, d_00607E84);
        d_006C870C = sub_00448F10(d_006C8714, effect);
        imp_00607330(effect);
    }
    d_006C8710++;
    verts[0] = a1;
    verts[1] = a2;
    verts[2] = a3;
    verts[3] = a4;
    verts[4] = a5;
    verts[5] = a6;
    hr = ((create_425980)(*(void ***)DEV)[0x68 / 4])(DEV, 0x18, 8, 2, 1, s + 0x1c4, 0);
    sub_00458940(hr, d_00607E74, 0x48);
    vb = *(void **)(s + 0x1c4);
    vt = *(void ***)vb;
    if (((lock_425980)vt[0x2c / 4])(vb, 0, 0x18, &data, 0) >= 0) {
        data[0] = verts[0];
        data[1] = verts[1];
        data[2] = verts[2];
        data[3] = verts[3];
        data[4] = verts[4];
        data[5] = verts[5];
        ((unlock_425980)vt[0x30 / 4])(vb);
        *(unsigned int *)(s + 0x1c8) = shader;
    }
    return s;
}
