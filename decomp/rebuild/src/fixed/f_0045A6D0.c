/* 0x0045A6D0: the world camera's update: key presses (this +0x7C: +0x660 events of {key, down}, +0x664 of them;
 * not the console key +0x10A): space toggles +0x1D0 (mirrored in +0xDC's +0x1D4), right / left (and the arrow keys
 * held, state +0x110 / +0x118) step +0xDC's selection (0x004306D0, its EAX input only passed through) and refresh
 * +0x84 (0x004F7C60), ` and 1-0 pick +0xDC's +0x1D0 (0, 1-10), Tab 0x00459520 on +0xEC; Ctrl+Q or Escape asks the
 * game (+0x38) to quit (+0xAC = 3, +0xB1). Zoom (0x00459C30), turn by keys +0x107 / +0x106 (the camera's +0x60 by
 * 0x0060B7A0), 0x00459B40, then the pan step (speeds +0x12C..+0x134 times inputs +0x124 / +0x128 / +0x120 times dt,
 * kept in the statics 0x006C8E24..) turned by the heading (-+0x60 times 0x00608528: _CIsin / _CIcos) is added to the
 * camera's +0x50..+0x58. Returns what the original leaves in EAX (0x00459B40's result) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004306D0(void *self, unsigned int eax, int step);
DECOMP_C int __thiscall sub_004F7C60(void *self);
DECOMP_C unsigned int __thiscall sub_00459520(void *self);
DECOMP_C int __thiscall sub_00459B40(void *self);
DECOMP_C void __thiscall sub_00459C30(void *self);
DECOMP_C double decomp_CIcos(double), decomp_CIsin(double);
DECOMP_C char d_0060B7A0[], d_006C8E30[], d_006C8E24[], d_006C8E28[], d_006C8E2C[], d_00608528[];

#define F(o) (*(float *)(s + (o)))
#define DC (*(char **)(s + 0xdc))

static void step_45A6D0(char *s, int d)
{
    sub_004306D0(DC, 0, d);
    sub_004F7C60(s + 0x84);
}

DECOMP(0045A6D0)
int __thiscall f_0045A6D0(void *this)
{
    char *s = (char *)this, *kb = *(char **)(s + 0x7c), *ev = *(char **)(kb + 0x660), *cam, *g;
    unsigned int n = *(unsigned int *)(kb + 0x664), i;
    float ang, sn, cs, x, y, z, dx, dz;
    int r;
    for (i = 0; i < n; i++) {
        unsigned char k = (unsigned char)ev[i * 2];
        if (!ev[i * 2 + 1] || k == (unsigned char)s[0x10a])
            continue;
        if (k == 0x39) {
            s[0x1d0] = !s[0x1d0];
            DC[0x1d4] = s[0x1d0];
        } else if (k == 0xcd)
            step_45A6D0(s, 1);
        else if (k == 0xcb)
            step_45A6D0(s, -1);
        else if (k == 0x29)
            *(int *)(DC + 0x1d0) = 0;
        else if (k >= 2 && k <= 0xb)
            *(int *)(DC + 0x1d0) = k - 1;
        else if (k == 0xf)
            sub_00459520(*(void **)(s + 0xec));
    }
    kb = *(char **)(s + 0x7c);
    if (kb[0x110] & 0x80)
        step_45A6D0(s, 1);
    kb = *(char **)(s + 0x7c);
    if (kb[0x118] & 0x80)
        step_45A6D0(s, -1);
    kb = *(char **)(s + 0x7c);
    if ((((kb[0x65] & 0x80) || (kb[0xe5] & 0x80)) && (kb[0x58] & 0x80)) || (kb[0x49] & 0x80)) {
        g = *(char **)(s + 0x38);
        *(int *)(g + 0xac) = 3;
        g[0xb0] = 0;
        g[0xb1] = 1;
    }
    sub_00459C30(this);
    kb = *(char **)(s + 0x7c);
    cam = *(char **)(s + 0x100);
    if (kb[0x48 + (unsigned char)s[0x107]] & 0x80) {
        cam[0x70] = 1;
        *(float *)(cam + 0x60) = (float)(*(float *)(cam + 0x60) + *(double *)d_0060B7A0);
    } else if (kb[0x48 + (unsigned char)s[0x106]] & 0x80) {
        cam[0x70] = 1;
        *(float *)(cam + 0x60) = (float)(*(float *)(cam + 0x60) - *(double *)d_0060B7A0);
    }
    r = sub_00459B40(this);
    if (!(*(unsigned int *)d_006C8E30 & 1))
        *(unsigned int *)d_006C8E30 |= 1;
    *(float *)d_006C8E24 = F(0x12c) * F(0x124) * F(0x40);
    *(float *)d_006C8E28 = F(0x130) * F(0x128) * F(0x40);
    *(float *)d_006C8E2C = F(0x134) * F(0x120) * F(0x40);
    cam = *(char **)(s + 0x100);
    ang = (float)(-*(float *)(cam + 0x60) * *(double *)d_00608528);
    sn = (float)decomp_CIsin(ang);
    cs = (float)decomp_CIcos(ang);
    x = *(float *)d_006C8E24;
    y = *(float *)d_006C8E28;
    z = *(float *)d_006C8E2C;
    cam[0x70] = 1;
    dz = cs * z - sn * x;
    dx = x * cs + sn * z;
    *(float *)(cam + 0x50) = dx + *(float *)(cam + 0x50);
    *(float *)(cam + 0x54) = *(float *)(cam + 0x54) + y;
    *(float *)(cam + 0x58) = *(float *)(cam + 0x58) + dz;
    return r;
}
