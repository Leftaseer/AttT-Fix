/* 0x0042E440: a thrown projectile's constructor (owner arg 1, model index arg 2, arg 3 for the owner's pose, speed
 * arg 4, trail arg 5): the 3D object base "Arrow" (0x004AD180), its vtable, an empty mesh list (+0x1C4), a flat arc
 * (+0x254, 0x0042DC20), the constants +0x2CC / +0x2D0, the speed +0x2BC and owner +0x2C4; the owner's model parts
 * (+0x1DC, 0x004B6450 of them) give their mesh of index arg 2 (made visible, +0x24 cleared) to the list (push_back
 * inline, 0x00487860 when full); the first mesh's pose (0x0042DA70 with the owner's +0x1EC and arg 3) scaled by
 * 0x00608A70 (D3DXMatrixScaling, D3DXMatrixMultiply) is its matrix (+0x1D4); not flying (+0x2C0), time 0 (+0x2D4);
 * a new 0x690-byte trail (0x00550420 with an empty name) at +0x2C8 gets arg 5 (0x0054EA10) and the rate 0x00608C1C
 * (0x0054D350, which takes 0x0054EA10's result in EAX as the original leaves it). Returns this */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_0042DC20(void *self, float x0, float y0, float z0, float x1, float y1, float z1,
                                      float a7, float k);
DECOMP_C unsigned int __thiscall sub_004B6450(void *self);
DECOMP_C void __thiscall sub_00487860(void *self, void *where, unsigned int n, void *val);
DECOMP_C float *__thiscall sub_0042DA70(void *self, void *out, void *a, void *b);
DECOMP_C float *__stdcall sub_005B8044(float *out, float x, float y, float z);       /* D3DXMatrixScaling */
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);     /* D3DXMatrixMultiply */
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C void __cdecl sub_0054D350(void *self, int eax, float rate);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_00608C28[], d_00608B5C[], d_00608C24[], d_00608C20[], d_00608A70[], d_0060FA8B[], d_00608C1C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0042E440)
void *__thiscall f_0042E440(void *this, char *owner, int model, void *pose, unsigned int speed, void *trail)
{
    char *s = (char *)this, *parts, *mesh, *v = s + 0x1c4;
    unsigned int str[7], k, ms[16], r[16];
    float *m, sc;
    void *o;
    imp_00607324(str, d_00608C28);
    sub_004AD180(this, str, 0, 0);
    imp_00607330(str);
    *(void **)s = d_00608B5C;
    *(int *)(v + 4) = 0;
    *(int *)(v + 8) = 0;
    *(int *)(v + 0xc) = 0;
    sub_0042DC20(s + 0x254, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f);
    *(unsigned int *)(s + 0x2cc) = *(unsigned int *)d_00608C24;
    *(unsigned int *)(s + 0x2bc) = speed;
    *(unsigned int *)(s + 0x2d0) = *(unsigned int *)d_00608C20;
    *(char **)(s + 0x2c4) = owner;
    parts = owner + 0x1dc;
    for (k = 0; k < sub_004B6450(parts); k++) {
        void **b;
        unsigned int n;
        mesh = (*(char ***)((*(char ***)(parts + 4))[k] + 8))[model];
        mesh[0x24] = 0;
        b = *(void ***)(v + 4);
        n = b ? (unsigned int)((char *)*(void ***)(v + 8) - (char *)b) >> 2 : 0;
        if (b && n < (unsigned int)((char *)*(void ***)(v + 0xc) - (char *)b) >> 2) {
            **(void ***)(v + 8) = mesh;
            *(void ***)(v + 8) += 1;
        } else
            sub_00487860(v, *(void **)(v + 8), 1, &mesh);
    }
    m = sub_0042DA70(**(void ***)(s + 0x1c8), r, *(void **)(*(char **)(s + 0x2c4) + 0x1ec), pose);
    __builtin_memcpy(s + 0x1d4, m, 64);
    sc = *(float *)d_00608A70;
    sub_005B8044((float *)ms, sc, sc, sc);
    sub_005B8020((float *)r, ms, s + 0x1d4);
    __builtin_memcpy(s + 0x1d4, r, 64);
    s[0x2c0] = 0;
    *(float *)(s + 0x2d4) = 0.0f;
    o = sub_005E3EAE(0x690);
    if (o) {
        imp_00607324(str, d_0060FA8B);
        o = sub_00550420(o, str, 0, 0);
        *(void **)(s + 0x2c8) = o;
        imp_00607330(str);
    } else
        *(void **)(s + 0x2c8) = 0;
    sub_0054D350(*(void **)(s + 0x2c8), sub_0054EA10(*(void **)(s + 0x2c8), trail), *(float *)d_00608C1C);
    return this;
}
