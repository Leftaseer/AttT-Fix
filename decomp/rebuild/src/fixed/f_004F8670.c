/* 0x004F8670: a water surface's constructor (model name, reflection size, scene, arg 4 kept at +0x210): the 3D object
 * base (0x00430850), its vtable 0x00612DF4, the hero (0x00425F60, +0x214), the "WaterRipple" effect (0x004AB810), the
 * model (0x0047CC30 of 0x006C88C4, +0x1C4, its name into +8). The first water (count 0x006CA850) creates the shared
 * reflection target (0x006CA854: 0x004DF860 square of the size, retried without its fourth flag when vf30 fails), the
 * mouse (0x00421680 -> 0x006CA85C), a RenderToSurface (0x006CA858) like its surface (desc +0x1E0) with a depth buffer,
 * and the projection 0x006CA860 for half the camera's (0x006CA2C4) field of view (+0x74 * 0x00608528) and the screen's
 * aspect (0x006C8958 / 0x006C895C, 0x00612EE8). The effect (+0x3C) gets dwProjClearColor (+0x20C), mProj and tProj; a
 * "WaterCircle" (0x70 bytes, 0x004F92D0) is added to the scene (0x004205C0); +0x220, +0x264 cleared, +0x1DC set, and
 * "Water" is applied (0x004F8360). Returns this */
/* @conv ECX 16 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4F8670;                 /* std::string */
DECOMP_C void __thiscall sub_00430850(void *self);
DECOMP_C void *__cdecl sub_00425F60(void);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_0047CC30(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_004DF860(void *self, unsigned int w, unsigned int h, int a, int b, unsigned int fmt,
                                       int c);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C int __stdcall sub_005B8050(void *dev, unsigned int w, unsigned int h, unsigned int fmt, int depth,
                                    unsigned int dfmt, void **out);   /* D3DXCreateRenderToSurface */
DECOMP_C void *__thiscall sub_004F92D0(void *self, Str_4F8670 name, void *scene);
DECOMP_C void __thiscall sub_004205C0(void *self, void *obj);
DECOMP_C void __thiscall sub_004F8360(void *self, void *name);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C double decomp_CItan(double);
DECOMP_C char d_00612DF4[], d_00612F40[], d_006C88C4[], d_006CA850[], d_006CA854[], d_006CA85C[], d_006CA858[],
    d_006C8C10[], d_006CA2C4[], d_00608528[], d_00607CE0[], d_0068AE40[], d_00608A70[], d_006C8958[], d_006C895C[],
    d_00612EE8[], d_006CA860[], d_00612F2C[], d_00612EF0[], d_00612F24[], d_00612F18[], d_00610000[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef int (__thiscall *vf_4F8670)(void *self);
typedef int (__thiscall *del_4F8670)(void *self, int del);
typedef int (__stdcall *getsurf_4F8670)(void *tex, unsigned int level, void **out);
typedef int (__stdcall *desc_4F8670)(void *surf, void *desc);
typedef int (__stdcall *rel_4F8670)(void *o);
typedef void (__thiscall *setp_4F8670)(void *self, const char *name, const void *v);
typedef void (__thiscall *sets_4F8670)(void *self, void *name, void *v);

#define VT(o) (*(void ***)(o))
#define G(a) (*(float *)(d_006CA860 + (a) - 0x860))

static void *target_4F8670(unsigned int size, int flag)
{
    void *o = sub_005E3EAE(0x54);
    return o ? sub_004DF860(o, size, size, 1, flag, 0x15, 0) : 0;
}

DECOMP(004F8670)
void *__thiscall f_004F8670(void *this, void *name, unsigned int size, void *scene, unsigned int a4)
{
    char *s = (char *)this, *t, *fx;
    unsigned int str[7];
    void *res, *o;
    sub_00430850(this);
    *(void **)s = d_00612DF4;
    *(unsigned int *)(s + 0x210) = a4;
    *(void **)(s + 0x214) = sub_00425F60();
    imp_00607324(str, d_00612F40);
    sub_004AB810(this, str, 1);
    imp_00607330(str);
    res = sub_0047CC30(*(void **)d_006C88C4, name, 5);
    *(void **)(s + 0x1c4) = res;
    imp_0060731C(s + 8, res);
    if (!*(unsigned short *)d_006CA850) {
        void *surf;
        float fov, ys, asp;
        *(void **)d_006CA854 = target_4F8670(size, 1);
        t = *(char **)d_006CA854;
        if (!((vf_4F8670)VT(t)[0x30 / 4])(t)) {
            t = *(char **)d_006CA854;
            if (t)
                ((del_4F8670)VT(t)[0])(t, 1);
            *(void **)d_006CA854 = target_4F8670(size, 0);
        }
        *(void **)d_006CA85C = sub_00421680();
        t = *(char **)d_006CA854;
        t = (char *)((vf_4F8670)VT(t)[0x2c / 4])(t);
        ((getsurf_4F8670)VT(t)[0x48 / 4])(t, 0, &surf);
        ((desc_4F8670)VT(surf)[0x30 / 4])(surf, s + 0x1e0);
        sub_005B8050(*(void **)d_006C8C10, *(unsigned int *)(s + 0x1f8), *(unsigned int *)(s + 0x1fc),
                     *(unsigned int *)(s + 0x1e0), 1, 0x4b, (void **)d_006CA858);
        ((rel_4F8670)VT(surf)[2])(surf);
        fov = *(float *)(*(char **)d_006CA2C4 + 0x74);
        fov = (float)(fov * *(double *)d_00608528 * *(double *)d_00607CE0);
        fov = (float)decomp_CItan(fov);
        ys = 1.0f / fov;
        G(0x864) = 0;
        G(0x868) = 0;
        G(0x86c) = 0;
        G(0x870) = 0;
        G(0x878) = 0;
        G(0x87c) = 0;
        G(0x880) = *(float *)d_0068AE40;
        asp = (float)(*(float *)d_006C8958 * *(double *)d_00612EE8 / *(float *)d_006C895C);
        G(0x860) = asp * ys;
        G(0x874) = (float)(ys * *(double *)d_00612EE8);
        G(0x884) = 1.0f + 0.0f;
        G(0x888) = *(float *)d_00608A70;
        G(0x88c) = 0;
        G(0x890) = 0;
        G(0x894) = 0;
        G(0x898) = 0;
        G(0x89c) = *(float *)d_0068AE40;
    }
    *(unsigned short *)d_006CA850 += 1;
    fx = *(char **)(s + 0x3c);
    ((setp_4F8670)VT(fx)[0x30 / 4])(fx, d_00612F2C, s + 0x20c);
    fx = *(char **)(s + 0x3c);
    ((setp_4F8670)VT(fx)[0x50 / 4])(fx, d_00612EF0, d_006CA860);
    imp_00607324(str, d_00612F24);
    fx = *(char **)(s + 0x3c);
    ((sets_4F8670)VT(fx)[0xc / 4])(fx, str, *(void **)d_006CA854);
    imp_00607330(str);
    o = sub_005E3EAE(0x70);
    if (o) {
        Str_4F8670 n;
        imp_00607324(&n, d_00612F18);
        o = sub_004F92D0(o, n, scene);
    }
    sub_004205C0(scene, o);
    *(unsigned int *)(s + 0x220) = 0;
    *(float *)(s + 0x264) = 0;
    s[0x1dc] = 1;
    imp_00607324(str, d_00610000);
    sub_004F8360(this, str);
    imp_00607330(str);
    return this;
}
