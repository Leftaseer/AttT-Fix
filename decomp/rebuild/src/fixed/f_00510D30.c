/* 0x00510D30: Lua CalcWD(n): the melee counterpart of CalcWRD (0x00510D30): the target must be reachable
 * (0x0051DBF0 on its +0x98), the search uses the attack reach (0x00504400, +0x15C map, 0x005019E0, 0x004FB800 with 1)
 * and the shooter's "Damage"; when the scapegoat is not settled, it is 0 if the target cannot be reached but some
 * other square can (0x0051D6D0(0, 0), 0x0051DBF0 by number) or another group but not the target can be taken
 * (0x0050E800 attacking). The number is pushed; returns 1 */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Obj12_510D30;
typedef struct { unsigned int alloc; char *head; unsigned int size; } Set_510D30;
typedef struct { unsigned int w[3]; } Tbl_510D30;
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);             /* lua_tonumber */
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void __thiscall sub_004FB320(void *self);
DECOMP_C void __thiscall sub_00504400(void *self, void *unit, void *first);
DECOMP_C char __thiscall sub_0051DBF0(void *self, void *map, int a);
DECOMP_C void *__thiscall sub_00503BC0(void *self, void *key);   /* map lookup by *key */
DECOMP_C void *__thiscall sub_00502D10(void *self, void *key);
DECOMP_C void __thiscall sub_005019E0(void *self, void *src);
DECOMP_C void *__cdecl sub_004E46D0(void);
DECOMP_C void *__thiscall sub_004FB800(void *self, void *out, Obj12_510D30 reach, int attack);
DECOMP_C void __thiscall sub_0050A650(void *self, void *src);
DECOMP_C void __thiscall sub_004FB2C0(void *self);
DECOMP_C void __thiscall sub_004FA240(void *self);
DECOMP_C void __thiscall sub_004FAF90(void *self, void *out, void *first, void *last);
DECOMP_C void *__thiscall sub_00508770(void *self, Tbl_510D30 *out);
DECOMP_C unsigned char __thiscall sub_0057ABB0(void *self, const char *key, int def);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void __thiscall sub_0051D6D0(void *self, int a, int b);
DECOMP_C unsigned char __thiscall sub_0050E800(void *self, char *unit, char *grp, unsigned char attack);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_008D122C[], d_00613B58[], d_00613B44[], d_0060AB58[], d_00613BC8[], d_0068AE08[], d_006095F8[],
    d_0060826C[], d_00607CB8[];

#define SELU (*(char **)(s + 0x64))

static int scape_510D30(void)
{
    Tbl_510D30 t;
    int r = sub_0057ABB0(sub_004323E0(&t, d_0060AB58), d_00613B44, 0) == 1;
    sub_004220A0(&t);
    return r;
}

static float ratio_510D30(char *s, float total)
{
    Tbl_510D30 t;
    float dmg;
    unsigned int n;
    float nf;
    dmg = sub_0057AD40(sub_00508770(**(void ***)(SELU + 0x58), &t), d_00613BC8);
    n = sub_0051DAA0(SELU);
    nf = (float)(int)n;
    if ((int)n < 0)
        nf += *(float *)d_0068AE08;
    dmg = nf * dmg;
    sub_004220A0(&t);
    return (float)(total / dmg + *(double *)d_006095F8);
}

DECOMP(00510D30)
int __thiscall f_00510D30(void *this, char *st)
{
    char *s = (char *)this, *u;
    float res = 0.0f;
    int n;
    struct { void *vt; void *child; int a; } o;
    n = (int)(long long)sub_00402DE0(*(void **)d_008D122C, *(int *)(st + 0x10) + 1) - 1;
    if (n < *(int *)(s + 0x54))
        u = *(char **)(s + 0x50) + n * 0xc8;
    else
        u = *(char **)(s + 0x5c) + (n - *(int *)(s + 0x54)) * 0xc8;
    if (u != SELU && *(int *)(u + 0x94) != 1 && *(float *)(u + 0xa8) != *(double *)d_00613B58 &&
        sub_0051DBF0(SELU, *(void **)(u + 0x98), 0)) {
        Set_510D30 p;
        Tbl_510D30 t1;
        char *it, *dummy;
        void *first = **(void ***)(u + 0x58), *r;
        float total = 0.0f;
        unsigned int res3[3];
        Obj12_510D30 reach;
        int blocked;
        sub_004FB320(&p);
        sub_00504400(*(void **)(s + 0xd8), SELU, first);
        r = sub_00502D10(sub_00503BC0(*(char **)(s + 0xd8) + 0x15c, s + 0x64), &first);
        sub_005019E0(&reach, r);
        sub_0050A650(&p, sub_004FB800(sub_004E46D0(), res3, reach, 1));
        sub_004FB2C0(res3);
        for (it = *(char **)p.head; it != p.head;) {
            unsigned int c = *(unsigned int *)(it + 0x10);
            float cf = (float)(int)c;
            if ((int)c < 0)
                cf += *(float *)d_0068AE08;
            total = cf + total;
            sub_004FA240(&it);
        }
        sub_00508770(**(void ***)(u + 0x58), &t1);
        if (!sub_0057ABB0(&t1, d_00613B44, 0) && scape_510D30())
            res = 0.0f;
        else {
            if (scape_510D30() && sub_0057ABB0(&t1, d_00613B44, 0) == 1)
                res = ratio_510D30(s, total);
            else {
                unsigned int i, cnt = *(unsigned int *)(s + 0x54);
                int any = 0, other = 0;
                sub_0051D6D0(SELU, 0, 0);
                for (i = 0; i < *(unsigned int *)(s + 0x54); i++)
                    if (sub_0051DBF0(SELU, (void *)(size_t)i, 0)) {
                        any = 1;
                        break;
                    }
                blocked = !sub_0051DBF0(SELU, *(void **)(u + 0x98), 0) && any;
                if (blocked)
                    res = 0.0f;
                else {
                    for (i = 0; i < *(unsigned int *)(s + 0x54); i++)
                        if (sub_0050E800(this, SELU, *(char **)(s + 0x50) + i * 0xc8, 1)) {
                            other = 1;
                            break;
                        }
                    if (!sub_0050E800(this, SELU, u, 1) && other)
                        res = 0.0f;
                    else
                        res = ratio_510D30(s, total);
                }
            }
            sub_0051D6D0(SELU, 1, 1);
        }
        sub_004220A0(&t1);
        sub_004FAF90(&p, &dummy, *(char **)p.head, p.head);
        sub_005E3E9C(p.head);
    }
    o.child = 0;
    o.vt = d_0060826C;
    o.a = 0;
    sub_004030A0(*(void **)d_008D122C, res);
    o.a = 1;
    o.vt = d_00607CB8;
    sub_00422000(&o);
    return 1;
}
