/* 0x00525C00: a battle border's setup (army list arg 1, model arg 2, arg 3 for the markers, centre x / z args 5 / 7,
 * name arg 9; args 4, 6 and 8 unused): keeps the name (+0x38) and centre (+0x54 / +0x58); the GUI's
 * BorderStandartPoint entry for the name (0x005608F0, 0x00561830; refcounted) lists point ranges (pairs of numbers,
 * 0x005605D0 / 0x0055F4A0): each point of the model (arg 2's +0x2C: 32-byte points +0x28, count +0x24) in a range
 * gets a new 0x23C-byte marker (0x004CBE20) placed there (0x004AC940, vf38(arg 3, 0)) facing away from the centre
 * (atan2 in 0..2pi times 0x00609628, +0x78) and added to arg 1 (+4's vf4); then every point becomes a vertex of the
 * border polygon (+0xC0, 0x0047F760), a point (+0x60 / +0x64) and the normalised direction to the centre
 * (D3DXVec2Normalize, +0x6C / +0x70). A scratch array (vtable 0x00613600) of the point count is allocated and freed */
/* @conv ECX 36 */
#include "auto_pre.h"
typedef struct { float x, y; } V2_525C00;
DECOMP_C void *__cdecl sub_005608F0(void);
DECOMP_C char *__thiscall sub_00561830(void *self, void *name);
DECOMP_C unsigned int __thiscall sub_005605D0(void *self);
DECOMP_C float __thiscall sub_0055F4A0(void *self, float i);
DECOMP_C void *__thiscall sub_004CBE20(void *self);
DECOMP_C void __thiscall sub_004AC940(void *self, float x, float z);
DECOMP_C V2_525C00 *__thiscall sub_004205A0(V2_525C00 *self, float x, float y);
DECOMP_C void __thiscall sub_0047F760(void *self, void *pt);
DECOMP_C float *__stdcall sub_005B80C8(float *out, const float *v);           /* D3DXVec2Normalize */
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                       /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *p);                                  /* operator delete[] */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C double decomp_CIatan2(double y, double x);
DECOMP_C char d_00614AC8[], d_00613600[], d_0068AE08[], d_0068AE00[], d_006095F0[], d_00609628[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef void (__thiscall *place_525C00)(void *self, unsigned int a, int b);
typedef void (__thiscall *add_525C00)(void *self, void *o);
typedef void (__thiscall *del_525C00)(void *self, int del);

static unsigned int bytes_525C00(unsigned int n, unsigned int sz)
{
    unsigned long long b = (unsigned long long)n * sz;
    return b >> 32 ? 0xffffffff : (unsigned int)b;
}

static char *ref_525C00(char *p)
{
    if (p)
        *(int *)(p + 4) += 1;
    return p;
}

static void unref_525C00(char *p)
{
    if (p && !(*(int *)(p + 4) -= 1))
        ((del_525C00)**(void ***)p)(p, 1);
}

static void *array_525C00(char *s, int off, unsigned int n)
{
    if (*(void **)(s + off)) {
        sub_005E3EBA(*(void **)(s + off));
        *(void **)(s + off) = 0;
    }
    if (n)
        *(void **)(s + off) = sub_005E3B10(bytes_525C00(n, 8));
    *(unsigned int *)(s + off + 4) = 0;
    return *(void **)(s + off);
}

DECOMP(00525C00)
void __thiscall f_00525C00(void *this, char *armies, char *model, unsigned int a3, unsigned int a4, float cx,
                           unsigned int a6, float cz, unsigned int a8, void *name)
{
    char *s = (char *)this, *mesh, *pts, *el, *el2;
    struct { void *vt; void *data; unsigned int size; } tmp;
    unsigned int str[7], j, n;
    imp_0060731C(s + 0x38, name);
    *(float *)(s + 0x54) = cx;
    *(float *)(s + 0x58) = cz;
    mesh = *(char **)(model + 0x2c);
    pts = *(char **)(mesh + 0x28);
    imp_00607324(str, d_00614AC8);
    el = ref_525C00(sub_00561830(sub_005608F0(), str));
    imp_00607330(str);
    el2 = ref_525C00(sub_00561830(el, s + 0x38));
    tmp.vt = d_00613600;
    tmp.data = sub_005E3B10(bytes_525C00(*(unsigned int *)(mesh + 0x24), 4));
    tmp.size = 0;
    for (j = 1; j <= sub_005605D0(el2); j += 2) {
        float f = (float)(int)j, f2;
        unsigned int lo, hi, k;
        if ((int)j < 0)
            f += *(float *)d_0068AE08;
        lo = (unsigned int)(long long)sub_0055F4A0(el2, f);
        f2 = (float)(f + *(double *)d_0068AE00);
        hi = (unsigned int)(long long)sub_0055F4A0(el2, f2);
        if (lo > hi)
            continue;
        for (k = lo; k <= hi; k++) {
            float *p = (float *)(pts + k * 0x20), dx, dz, ang;
            char *o = sub_005E3EAE(0x23c);
            o = o ? sub_004CBE20(o) : 0;
            sub_004AC940(o, p[0], p[2]);
            ((place_525C00)(*(void ***)o)[0x38 / 4])(o, a3, 0);
            dx = *(float *)(s + 0x54) - *(float *)(o + 0x64);
            dz = *(float *)(s + 0x58) - *(float *)(o + 0x6c);
            ang = (float)decomp_CIatan2(dx, dz);
            if (0.0f > dx)
                ang = (float)(ang + *(double *)d_006095F0);
            o[0x80] = 1;
            *(float *)(o + 0x78) = (float)(ang * *(double *)d_00609628);
            ((add_525C00)(*(void ***)(armies + 4))[1])(armies + 4, o);
        }
    }
    n = *(unsigned int *)(mesh + 0x24);
    array_525C00(s, 0x60, n);
    n = *(unsigned int *)(mesh + 0x24);
    array_525C00(s, 0x6c, n);
    for (j = 0; j < *(unsigned int *)(mesh + 0x24); j++) {
        float *p = (float *)(pts + j * 0x20);
        V2_525C00 v, d, *q;
        sub_0047F760(s + 0xc0, sub_004205A0(&v, p[0], p[2]));
        q = (V2_525C00 *)*(void **)(s + 0x60) + *(unsigned int *)(s + 0x64);
        q->x = p[0];
        q->y = p[2];
        *(unsigned int *)(s + 0x64) += 1;
        q = (V2_525C00 *)*(void **)(s + 0x60) + j;
        d.x = *(float *)(s + 0x54) - q->x;
        d.y = *(float *)(s + 0x58) - q->y;
        sub_005B80C8(&d.x, &d.x);
        ((V2_525C00 *)*(void **)(s + 0x6c))[*(unsigned int *)(s + 0x70)] = d;
        *(unsigned int *)(s + 0x70) += 1;
    }
    if (tmp.data)
        sub_005E3EBA(tmp.data);
    unref_525C00(el2);
    unref_525C00(el);
}
