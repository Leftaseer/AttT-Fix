/* 0x0050EA50: Lua CalcWRD(n): the ratio for the selected unit (+0x64) shooting at battle group n (1-based: our +0x50
 * groups first, then the enemy's +0x5C; 0xC8-byte entries): 0 for itself, a group that is done (+0x94 == 1), one whose
 * +0xA8 is 0x00613B58, a non-shooter (+0x48) or one it cannot shoot (0x00508120); otherwise the group's health is the
 * sum of the counts (+0x10) the battle's search (0x004E46D0 / 0x004FB800 over the reach maps of +0xD8: 0x00503D20,
 * 0x00503BC0 by the unit, 0x00502D10 by the group's first member) leaves in a set, divided by the shooter's
 * RangeAttackDamage (its first member's table, 0x00508770) times its size (0x0051DAA0), plus 0x006095F8. It is 0
 * when the scapegoat was used (the group's or TacticLevel's usedScapegoat) and, without both set, when the shooter is
 * blocked (0x0051D6D0, +0x7C flags) and the target is not, or another group but not the target can be taken
 * (0x0050E800). The number is pushed (lua_pushnumber); returns 1 */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Obj12_50EA50;
typedef struct { unsigned int alloc; char *head; unsigned int size; } Set_50EA50;
typedef struct { unsigned int w[3]; } Tbl_50EA50;
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);             /* lua_tonumber */
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C unsigned char __cdecl sub_00508120(void *self, unsigned int eax, void *unit);
DECOMP_C void __thiscall sub_004FB320(void *self);
DECOMP_C void __thiscall sub_00503D20(void *self, void *unit, void *first);
DECOMP_C void *__thiscall sub_00503BC0(void *self, void *key);   /* map lookup by *key */
DECOMP_C void *__thiscall sub_00502D10(void *self, void *key);
DECOMP_C void __thiscall sub_00501B90(void *self, void *src);
DECOMP_C void *__cdecl sub_004E46D0(void);
DECOMP_C void *__thiscall sub_004FB800(void *self, void *out, Obj12_50EA50 reach, int attack);
DECOMP_C void __thiscall sub_0050A650(void *self, void *src);
DECOMP_C void __thiscall sub_004FB2C0(void *self);
DECOMP_C void __thiscall sub_004FA240(void *self);
DECOMP_C void __thiscall sub_004FAF90(void *self, void *out, void *first, void *last);
DECOMP_C void *__thiscall sub_00508770(void *self, Tbl_50EA50 *out);
DECOMP_C unsigned char __thiscall sub_0057ABB0(void *self, const char *key, int def);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void __thiscall sub_0051D6D0(void *self, int a, int b);
DECOMP_C unsigned char __thiscall sub_0050E800(void *self, char *unit, char *grp, unsigned char attack);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C char d_008D122C[], d_00613B58[], d_00613B44[], d_0060AB58[], d_00613B30[], d_0068AE08[], d_006095F8[],
    d_0060826C[], d_00607CB8[];

#define SELU (*(char **)(s + 0x64))

static int scape_50EA50(void)
{
    Tbl_50EA50 t;
    int r = sub_0057ABB0(sub_004323E0(&t, d_0060AB58), d_00613B44, 0) == 1;
    sub_004220A0(&t);
    return r;
}

static float ratio_50EA50(char *s, float total)
{
    Tbl_50EA50 t;
    float dmg;
    unsigned int n;
    float nf;
    dmg = sub_0057AD40(sub_00508770(**(void ***)(SELU + 0x58), &t), d_00613B30);
    n = sub_0051DAA0(SELU);
    nf = (float)(int)n;
    if ((int)n < 0)
        nf += *(float *)d_0068AE08;
    dmg = nf * dmg;
    sub_004220A0(&t);
    return (float)(total / dmg + *(double *)d_006095F8);
}

DECOMP(0050EA50)
int __thiscall f_0050EA50(void *this, char *st)
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
    if (u != SELU && *(int *)(u + 0x94) != 1 && *(float *)(u + 0xa8) != *(double *)d_00613B58 && SELU[0x48] &&
        sub_00508120(this, *(unsigned int *)(u + 0x94), SELU)) {
        Set_50EA50 p;
        Tbl_50EA50 t1;
        char *it, *dummy;
        void *first = **(void ***)(u + 0x58), *r;
        float total = 0.0f;
        unsigned int res3[3];
        Obj12_50EA50 reach;
        int blocked;
        sub_004FB320(&p);
        sub_00503D20(*(void **)(s + 0xd8), SELU, first);
        r = sub_00502D10(sub_00503BC0(*(char **)(s + 0xd8) + 0x150, s + 0x64), &first);
        sub_00501B90(&reach, r);
        sub_0050A650(&p, sub_004FB800(sub_004E46D0(), res3, reach, 0));
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
        if (!sub_0057ABB0(&t1, d_00613B44, 0) && scape_50EA50())
            res = 0.0f;
        else {
            if (scape_50EA50() && sub_0057ABB0(&t1, d_00613B44, 0) == 1)
                res = ratio_50EA50(s, total);
            else {
                unsigned int i, cnt = *(unsigned int *)(s + 0x54);
                int any = 0, other = 0;
                sub_0051D6D0(SELU, 1, 0);
                for (i = 0; i < cnt; i++)
                    if ((*(char **)(SELU + 0x7c))[i]) {
                        any = 1;
                        break;
                    }
                blocked = !(*(char **)(SELU + 0x7c))[*(int *)(u + 0x98)] && any;
                if (blocked)
                    res = 0.0f;
                else {
                    for (i = 0; i < *(unsigned int *)(s + 0x54); i++)
                        if (sub_0050E800(this, SELU, *(char **)(s + 0x50) + i * 0xc8, 0)) {
                            other = 1;
                            break;
                        }
                    if (!sub_0050E800(this, SELU, u, 0) && other)
                        res = 0.0f;
                    else
                        res = ratio_50EA50(s, total);
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
