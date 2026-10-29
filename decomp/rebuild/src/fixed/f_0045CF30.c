/* 0x0045CF30: House's render with two arguments (vf 0xDC): as Town::Render (0x0045CF30) without resetting the matrix stack:
 * vf B4(a1), its banner (+0x298, 0x00425710), vf BC(a1, a2) and vf B8, then (when the world is drawn) its matrix, the
 * model's box (fixed, or merged from its children and widened by 0x0060ACC0), the world matrix and the draw */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00425710(void *self);
DECOMP_C void __thiscall sub_0058EEE0(void *self);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C void __thiscall sub_00590070(void *self, const float *mn, const float *mx);
DECOMP_C void __thiscall sub_0058F0B0(void *self, const float *box);
DECOMP_C void __thiscall sub_0058FC30(void *self);
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C char d_006CA2D4[], d_006CA2D0[], d_006C8C10[], d_006C88D8[], d_006CA0A4[], d_0060ACC0[], d_0060B9C8[],
    d_0060B9C4[];
typedef void (__stdcall *ms0_45CF30)(void *self);
typedef void (__stdcall *ms1_45CF30)(void *self, const void *m);
typedef void *(__stdcall *top_45CF30)(void *self);
typedef void (__stdcall *set_45CF30)(void *self, unsigned int state, const void *m);
typedef void (__thiscall *v1_45CF30)(void *self, float a);
typedef void (__thiscall *v2_45CF30)(void *self, float a, float b);
typedef int (__thiscall *v0_45CF30)(void *self);

#define VT(o, n) ((*(void ***)(o))[(n) / 4])

DECOMP(0045CF30)
int __thiscall f_0045CF30(void *this, float a1, float a2)
{
    char *s = (char *)this, *ms, *m, *top;
    float mn[3], mx[3];
    ((v1_45CF30)VT(s, 0xb4))(s, a1);
    if (*(void **)(s + 0x298))
        sub_00425710(*(void **)(s + 0x298));
    ((v2_45CF30)VT(s, 0xbc))(s, a1, a2);
    ((v0_45CF30)VT(s, 0xb8))(s);
    if (!(*(char **)d_006C88D8)[0x40])
        return *(int *)d_006C88D8;
    ms = *(char **)d_006CA2D4;
    ((ms0_45CF30)VT(ms, 0x10))(ms);
    ms = *(char **)d_006CA2D4;
    ((ms1_45CF30)VT(ms, 0x20))(ms, s + 0x168);
    ms = *(char **)d_006CA2D4;
    top = (char *)((top_45CF30)VT(ms, 0x44))(ms);
    m = *(char **)(s + 0x1a8);
    *(char **)(s + 0x1c0) = top;
    if (*(int *)(s + 0x1b8)) {
        float h, box[0x18];
        char **head, **n;
        double k;
        sub_0058EEE0(m);
        top = *(char **)(s + 0x1c0);
        h = sub_00473110(*(void **)d_006CA2D0, *(float *)(top + 0x30), *(float *)(top + 0x38));
        mn[0] = 0; mn[1] = h; mn[2] = 0;
        mx[0] = 0; mx[1] = h; mx[2] = 0;
        sub_00590070(*(void **)(s + 0x1a8), mn, mx);
        head = *(char ***)(s + 0x1b4);
        for (n = (char **)head[0]; n != *(char ***)(s + 0x1b4); n = (char **)n[0]) {
            char *e = n[2];
            unsigned int i;
            __builtin_memcpy(box, *(char **)(e + 0x1a8) + 0x1e4, sizeof box);
            for (i = 0; i < 0x60; i += 0xc) {
                float *v = (float *)((char *)box + i);
                sub_005B8026(v, v, e + 0x168);
                v[1] = *(float *)(*(char **)(e + 0x1a8) + 0x248 + i);
            }
            sub_0058F0B0(*(void **)(s + 0x1a8), box);
        }
        m = *(char **)(s + 0x1a8);
        k = *(double *)d_0060ACC0;
        mx[0] = (float)(*(float *)(m + 0x30c) + k);
        mx[1] = (float)(*(float *)(m + 0x310) + k);
        mx[2] = (float)(*(float *)(m + 0x314) + k);
        mn[0] = (float)(*(float *)(m + 0x300) - k);
        mn[1] = (float)(*(float *)(m + 0x304) - k);
        mn[2] = (float)(*(float *)(m + 0x308) - k);
        sub_00590070(m, mn, mx);
        *(float *)(*(char **)(s + 0x1c0) + 0x34) = 0;
    } else {
        float a = *(float *)d_0060B9C8, c = *(float *)d_0060B9C4;
        mn[0] = a; mn[1] = 0; mn[2] = a;
        mx[0] = c; mx[1] = c; mx[2] = c;
        sub_00590070(m, mn, mx);
        top = *(char **)(s + 0x1c0);
        *(float *)(*(char **)(s + 0x1c0) + 0x34) =
            (float)(sub_00473110(*(void **)d_006CA2D0, *(float *)(top + 0x30), *(float *)(top + 0x38)) +
                    *(float *)(s + 0x68));
    }
    m = *(char **)d_006C8C10;
    ((set_45CF30)VT(m, 0xb0))(m, 0x100, *(void **)(s + 0x1c0));
    *(void **)d_006CA0A4 = *(void **)(s + 0x1c0);
    sub_0058FC30(*(void **)(s + 0x1a8));
    return ((v0_45CF30)VT(s, 0xb8))(s);
}
