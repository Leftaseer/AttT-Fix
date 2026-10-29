/* 0x0044C840: Lua binding (L from 0x008D122C), the mirror of 0x0044C5A0: returns the world's (0x0042F160) +0x70
 * value (0x0044C340) when it has its +0x78; otherwise narrows the tree range by GUIScene.Options (the near end +0x2C
 * less (MaxFadeDist - MinFadeDist) * 0x00609E08, +0x30 = it plus 0x0060A208, the far end +0x34 less (MaxVisibleDist -
 * MinVisibleDist) times that, the step +0x38 "TreeVisibleDelta"); at or below MinFadeDist it settles there (+0x34
 * MinVisibleDist) and pushes 0, else pushes 0x00609648 * (1 - (MaxFadeDist - near) / (MaxFadeDist - MinFadeDist)),
 * truncated. Returns 1 (a temporary empty Object is made and destroyed, as the original does) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C int __thiscall sub_0044C340(void *self);
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_00422000(void *self);
DECOMP_C char d_008D122C[], d_0060826C[], d_00607CB8[], d_0060AD08[], d_0060AD00[], d_0060AD40[], d_0060AD30[],
    d_0060AD24[], d_0060AD14[], d_00609E08[], d_0060ACEC[], d_0060A208[], d_00609648[];

#define L (*(void **)d_008D122C)

DECOMP(0044C840)
int __cdecl f_0044C840(void)
{
    struct { void *vt; void *child; int a; } o;
    char *w = sub_0042F160(), *obj = *(char **)(w + 0x70);
    if (obj && *(void **)(obj + 0x78)) {
        int v = sub_0044C340(obj);
        o.child = 0;
        o.vt = d_0060826C;
        o.a = 0;
        sub_004030A0(L, (float)v);
    } else {
        unsigned int a1[3], b1[3], opt[3];
        struct { void *tbl; const char *key; } p;
        float maxf, maxv, minf, minv, t1, t2, s2;
        double dd;
        p.tbl = sub_004323E0(a1, d_0060AD08);
        p.key = d_0060AD00;
        sub_004369F0(&p, b1);
        sub_00435D90(opt, b1);
        sub_004220A0(b1);
        sub_004220A0(a1);
        maxf = sub_0057AD40(opt, d_0060AD40);
        maxv = sub_0057AD40(opt, d_0060AD30);
        minf = sub_0057AD40(opt, d_0060AD24);
        minv = sub_0057AD40(opt, d_0060AD14);
        dd = maxf - minf;
        t1 = (float)(dd * *(double *)d_00609E08);
        t2 = (float)((maxv - minv) * *(double *)d_00609E08);
        w = sub_0042F160();
        s2 = *(float *)(w + 0x2c) - t1;
        *(float *)(w + 0x2c) = s2;
        *(float *)(w + 0x30) = (float)(s2 + *(double *)d_0060A208);
        *(float *)(w + 0x34) = *(float *)(w + 0x34) - t2;
        *(float *)(w + 0x38) = sub_0057AD40(opt, d_0060ACEC);
        s2 = *(float *)(w + 0x2c);
        if (!(minf < s2)) {
            *(float *)(w + 0x30) = (float)(minf + *(double *)d_0060A208);
            *(float *)(w + 0x2c) = minf;
            *(float *)(w + 0x34) = minv;
            *(float *)(w + 0x38) = sub_0057AD40(opt, d_0060ACEC);
            o.child = 0;
            o.vt = d_0060826C;
            o.a = 0;
            sub_004030A0(L, 0.0f);
        } else {
            double x = (maxf - s2) / dd, k = *(double *)d_00609648;
            int v = (int)(long long)(k - x * k);
            o.child = 0;
            o.vt = d_0060826C;
            o.a = 0;
            sub_004030A0(L, (float)v);
        }
        o.a = 1;
        o.vt = d_00607CB8;
        sub_00422000(&o);
        sub_004220A0(opt);
        return 1;
    }
    o.a = 1;
    o.vt = d_00607CB8;
    sub_00422000(&o);
    return 1;
}
