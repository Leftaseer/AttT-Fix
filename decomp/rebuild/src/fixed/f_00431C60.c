/* 0x00431C60: a blood splash's constructor (from, to, drops vector, arg 4): the effect base "Blood" (0x00424D00 with
 * arg 4), its vtable 0x0060920C, an empty particle-system list (+0x38) and vector (+0x44, room for the drops), +0x54
 * set; the horizontal direction from -> to turned by 0x00609248 about Y is the axis about which each drop's (0x28-byte
 * elements, 0x00431AC0 of them) direction - towards "to" from "from" raised by the drop's height (+0x20), with that
 * height as its y - turns by its angle ((+0x24 - 0x00609240) * 0x00608528); each drop gets a new 0x690-byte "BloodPS"
 * system (0x00550420) loaded from the drop (0x0054EA10), placed at the raised point (provider +0x2E4), aimed along the
 * direction (provider +0x2CC), started with the drop's +0x1C (0x0054FE30) and appended to the list. Returns this */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00424D00(void *self, void *name, int flag);
DECOMP_C void **__cdecl sub_004C2F40(void);
DECOMP_C void __thiscall sub_004D6040(void *self, unsigned int n);
DECOMP_C unsigned int __thiscall sub_00431AC0(void *self);
DECOMP_C float *__stdcall sub_005B8032(float *out, float a);                          /* D3DXMatrixRotationY */
DECOMP_C void *__stdcall sub_005B8056(void *out, const float *axis, float angle);    /* D3DXMatrixRotationAxis */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C int __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C char d_0060924C[], d_0060920C[], d_00609248[], d_00609240[], d_00608528[], d_00609234[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *set_431C60)(void *obj, void *self, const void *val);

#define SET(p, v) ((set_431C60)((void **)(p))[4])(((void **)(p))[5], p, v)

DECOMP(00431C60)
void *__thiscall f_00431C60(void *this, const float *from, const float *to, char *drops, int a4)
{
    char *s = (char *)this, *v = s + 0x44, *e, **head, **nn;
    unsigned int str[7], i, off, n;
    float axis[3], m[16];
    char *b;
    imp_00607324(str, d_0060924C);
    sub_00424D00(this, str, a4);
    imp_00607330(str);
    *(void **)s = d_0060920C;
    *(void ***)(s + 0x3c) = sub_004C2F40();
    *(unsigned int *)(s + 0x40) = 0;
    *(unsigned int *)(v + 4) = 0;
    *(unsigned int *)(v + 8) = 0;
    *(unsigned int *)(v + 0xc) = 0;
    s[0x54] = 1;
    b = *(char **)(drops + 4);
    n = b ? (unsigned int)((*(char **)(drops + 8) - b) / 0x28) : 0;
    sub_004D6040(v, n);
    axis[0] = to[0] - from[0];
    axis[1] = 0.0f;
    axis[2] = to[2] - from[2];
    sub_005B8032(m, *(float *)d_00609248);
    sub_005B8026(axis, axis, m);
    axis[1] = 0.0f;
    for (i = 0, off = 0; i < sub_00431AC0(drops); i++, off += 0x28) {
        float p[3], d[3], ang;
        void *o, *ps;
        p[0] = from[0];
        p[1] = from[1];
        p[2] = from[2];
        e = *(char **)(drops + 4) + off;
        p[1] = *(float *)(e + 0x20) + p[1];
        d[0] = to[0] - p[0];
        d[1] = p[1];
        d[2] = to[2] - p[2];
        ang = (float)((*(float *)(e + 0x24) - *(double *)d_00609240) * *(double *)d_00608528);
        sub_005B8056(m, axis, ang);
        sub_005B8026(d, d, m);
        o = sub_005E3EAE(0x690);
        if (o) {
            imp_00607324(str, d_00609234);
            ps = sub_00550420(o, str, a4, 0);
            imp_00607330(str);
        } else
            ps = 0;
        sub_0054EA10(ps, *(char **)(drops + 4) + off);
        SET((char *)ps + 0x2e4, p);
        SET((char *)ps + 0x2cc, d);
        sub_0054FE30(ps, *(int *)(*(char **)(drops + 4) + off + 0x1c), 0.0f);
        head = *(char ***)(s + 0x3c);
        nn = sub_005AD6C0(head, (char **)head[1], &ps);
        sub_004E0EF0(s + 0x38, 1);
        head[1] = (char *)nn;
        *(char ***)nn[1] = nn;
    }
    return this;
}
