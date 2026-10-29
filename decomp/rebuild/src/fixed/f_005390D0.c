/* 0x005390D0: CWorldHeroCreature's follow step (state 1 of 0x005396E0): back at home (+0x204..+0x20C within +0x1FC,
 * squared, when 0x00538980 allows) or when the owner (+0x1CC) is neither in state 2 nor +0x1EB, or is +0x4E4, or the
 * creature is within +0x1F4 of home, it goes idle (the animation +0x1DC, 0x004CAFE0(0), state +0x1EC = 0). Otherwise it
 * faces home (0x00433250 on the offset, times 0x00609628 plus 0x006099D8; 0x004ACB80 speed 10) and moves: past +0x1F8
 * from a running owner (+0x210, 0x005388F0) by its model's speed (+0x1E4: 0x0042A950) times 0x0060A308 forward and
 * the owner's +0x4C0 times that sideways, turned by its heading (+0x84 times 0x00608528: _CIsin / _CIcos), else by the
 * model's step (0x0042AAB0); 0x004ACAC0 does the move. Returns what the original leaves in EAX */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char __thiscall sub_00538980(void *self);
DECOMP_C int __thiscall sub_004CAFE0(void *self, char a);
DECOMP_C double __cdecl sub_00433250(float *v);
DECOMP_C void __thiscall sub_004ACB80(void *self, float angle, int speed);
DECOMP_C char __thiscall sub_005388F0(void *self);
DECOMP_C float __thiscall sub_0042A950(void *self);
DECOMP_C float *__thiscall sub_0042AAB0(void *self, void *out, float speed);
DECOMP_C int __thiscall sub_004ACAC0(void *self, void *step);
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_00609628[], d_006099D8[], d_0060A308[], d_00608528[];
typedef float *(__thiscall *pos_5390D0)(void *self);

#define F(o) (*(float *)(s + (o)))
#define POS(o) ((pos_5390D0)(*(void ***)(o))[0x68 / 4])(o)

DECOMP(005390D0)
int __thiscall f_005390D0(void *this)
{
    char *s = (char *)this, *o;
    float *p, *q, dx, dz, d2, v[3], ang, a, b, spd, spd2, st[3];
    double zero;
    p = POS(this);
    dx = F(0x204) - p[0];
    dz = F(0x20c) - p[2];
    zero = 0.0 * 0.0;
    d2 = (float)(zero + dx * dx + dz * dz);
    if (F(0x1fc) > d2 && sub_00538980(this))
        goto idle;
    o = *(char **)(s + 0x1cc);
    if ((*(int *)(o + 0x1e4) != 2 && !o[0x1eb]) || o[0x4e4] || !(d2 > F(0x1f4)))
        goto idle;
    p = POS(this);
    v[0] = F(0x204) - p[0];
    v[1] = F(0x208) - p[1];
    v[2] = F(0x20c) - p[2];
    ang = (float)(sub_00433250(v) * *(double *)d_00609628 + *(double *)d_006099D8);
    sub_004ACB80(this, ang, 10);
    q = POS(*(void **)(s + 0x1cc));
    p = POS(this);
    dx = p[0] - q[0];
    dz = p[2] - q[2];
    if (s[0x210] && sub_005388F0(*(void **)(s + 0x1cc))) {
        d2 = (float)(dx * dx + zero + dz * dz);
        if (d2 > F(0x1f8)) {
            spd = (float)(sub_0042A950(*(void **)(s + 0x1e4)) * *(double *)d_0060A308);
            spd2 = (float)(*(double *)d_0060A308 * *(float *)(*(char **)(s + 0x1cc) + 0x4c0));
            ang = (float)(F(0x84) * *(double *)d_00608528);
            a = (float)decomp_CIsin(ang);
            b = (float)decomp_CIcos(ang);
            st[0] = spd * b + spd2 * a;
            st[1] = spd2 * b - a * spd;
            return sub_004ACAC0(this, st);
        }
    }
    return sub_004ACAC0(this, sub_0042AAB0(*(void **)(s + 0x1e4), st, F(0x84)));
idle:
    *(void **)(s + 0x1e8) = *(void **)(s + 0x1dc);
    {
        int r = sub_004CAFE0(*(void **)(s + 0x1dc), 0);
        *(int *)(s + 0x1ec) = 0;
        return r;
    }
}
