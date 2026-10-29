/* 0x0059D310: CDXUTDialog::OnRender (elapsed): its clock (+0x68) advances and a refresh request newer than its last
 * refresh (0x008D1240 > +0x64) refreshes it (0x00596590); when visible (+0x70) the manager's (0x00599A20) state block
 * is captured, blending set up and, unless minimized (+0x72), the background quad (x +0x174, y +0x178, width +0x17C,
 * height +0x180, corner colours +0x188 / +0x18C / +0x194 / +0x190) drawn as a fan of screen vertices (FVF 0x006C8280);
 * then the texture stages modulate, texture 0 (its node's +0x104) is set and the sprite begun; a caption (+0x71) draws
 * its element (+0x1CC) above the dialog and its text (+0x73, plus " (Minimized)") with a shadow; unless minimized the
 * controls (+0x1B4 / +0x1B8) render (vf0C) with the focused one (0x008D1244) last when it is this dialog's; the sprite
 * ends and the state block is applied. Returns S_OK */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00599A20(void);
DECOMP_C void __thiscall sub_00596590(void *self);
DECOMP_C void __thiscall sub_0059A180(void *self, void *el, void *rect);
DECOMP_C int __thiscall sub_0059A660(void *self, const void *text, char *el, const int *rect, unsigned char shadow,
                                     int count);
DECOMP_C int __stdcall sub_005933E0(char *dst, unsigned int size, const char *src);
DECOMP_C char d_008D1240[], d_006C8C10[], d_0060B874[], d_0068AE40[], d_006C8280[], d_0061FD00[], d_008D1244[];
typedef int (__stdcall *dev0_59D310)(void *o);
typedef int (__stdcall *dev1_59D310)(void *o, unsigned int a);
typedef int (__stdcall *dev2_59D310)(void *o, unsigned int a, unsigned int b);
typedef int (__stdcall *dev3_59D310)(void *o, unsigned int a, unsigned int b, unsigned int c);
typedef int (__stdcall *dpup_59D310)(void *o, unsigned int type, unsigned int n, const void *v, unsigned int stride);
typedef int (__thiscall *render_59D310)(void *self, void *dev, float elapsed);

#define VT(o) (*(void ***)(o))
#define RS(d, a, b) ((dev2_59D310)VT(d)[0xe4 / 4])(d, a, b)
#define TSS(d, a, b) ((dev3_59D310)VT(d)[0x10c / 4])(d, 0, a, b)

DECOMP(0059D310)
int __thiscall f_0059D310(void *this, float elapsed)
{
    char *s = (char *)this, *dev, *m, *node;
    float t, x, y, xw, yh, v[4][7];
    int i;
    t = elapsed + *(float *)(s + 0x68);
    *(float *)(s + 0x68) = t;
    if (*(float *)d_008D1240 > *(float *)(s + 0x64)) {
        *(float *)(s + 0x64) = t;
        sub_00596590(this);
    }
    if (!s[0x70])
        return 0;
    x = (float)*(int *)(s + 0x174);
    y = (float)*(int *)(s + 0x178);
    xw = *(int *)(s + 0x17c) + x;
    yh = *(int *)(s + 0x180) + y;
    for (i = 0; i < 4; i++) {
        v[i][2] = *(float *)d_0060B874;
        v[i][3] = *(float *)d_0068AE40;
    }
    v[0][0] = x;  v[0][1] = y;  *(unsigned int *)&v[0][4] = *(unsigned int *)(s + 0x188);
    v[0][5] = 0.0f;               v[0][6] = *(float *)d_0060B874;
    v[1][0] = xw; v[1][1] = y;  *(unsigned int *)&v[1][4] = *(unsigned int *)(s + 0x18c);
    v[1][5] = *(float *)d_0068AE40; v[1][6] = *(float *)d_0060B874;
    v[2][0] = xw; v[2][1] = yh; *(unsigned int *)&v[2][4] = *(unsigned int *)(s + 0x194);
    v[2][5] = *(float *)d_0068AE40; v[2][6] = *(float *)d_0068AE40;
    v[3][0] = x;  v[3][1] = yh; *(unsigned int *)&v[3][4] = *(unsigned int *)(s + 0x190);
    v[3][5] = 0.0f;               v[3][6] = *(float *)d_0068AE40;
    dev = *(char **)d_006C8C10;
    m = *(char **)sub_00599A20();
    ((dev0_59D310)VT(m)[0x10 / 4])(m);
    RS(dev, 0x1b, 1);                               /* ALPHABLENDENABLE */
    RS(dev, 0x13, 5);                               /* SRCBLEND = SRCALPHA */
    RS(dev, 0x14, 6);                               /* DESTBLEND = INVSRCALPHA */
    RS(dev, 0xf, 0);                                /* ALPHATESTENABLE */
    TSS(dev, 1, 3);
    TSS(dev, 3, 0);
    TSS(dev, 4, 2);
    TSS(dev, 5, 0);
    ((dev1_59D310)VT(dev)[0x170 / 4])(dev, 0);      /* SetVertexShader */
    ((dev1_59D310)VT(dev)[0x1ac / 4])(dev, 0);      /* SetPixelShader */
    RS(dev, 7, 0);                                  /* ZENABLE */
    if (!s[0x72]) {
        ((dev1_59D310)VT(dev)[0x164 / 4])(dev, *(unsigned int *)d_006C8280);
        ((dpup_59D310)VT(dev)[0x14c / 4])(dev, 6, 2, v, 0x1c);
    }
    TSS(dev, 1, 4);
    TSS(dev, 2, 2);
    TSS(dev, 3, 0);
    TSS(dev, 4, 4);
    TSS(dev, 5, 2);
    TSS(dev, 6, 0);
    ((dev3_59D310)VT(dev)[0x114 / 4])(dev, 0, 6, 2);   /* MINFILTER = LINEAR */
    if (!sub_00599A20())
        node = 0;
    else {
        int k = **(int **)(s + 0x19c);
        node = (*(char ***)(sub_00599A20() + 8))[k];
    }
    ((dev2_59D310)VT(dev)[0x104 / 4])(dev, 0, *(unsigned int *)(node + 0x104));
    m = *(char **)(sub_00599A20() + 4);
    ((dev1_59D310)VT(m)[0x20 / 4])(m, 1);
    if (s[0x71]) {
        int rc[4];
        char buf[0x100];
        rc[0] = 0;
        rc[1] = -*(int *)(s + 0x184);
        rc[2] = *(int *)(s + 0x17c);
        rc[3] = 0;
        sub_0059A180(this, s + 0x1cc, rc);
        rc[0] = 5;
        sub_005933E0(buf, 0x100, s + 0x73);
        if (s[0x72]) {
            unsigned int n;
            for (n = 0; n < 0x100 && buf[n]; n++)
                ;
            if (n < 0x100)
                sub_005933E0(buf + n, 0x100 - n, d_0061FD00);
        }
        sub_0059A660(this, buf, s + 0x1cc, rc, 1, -1);
    }
    if (!s[0x72]) {
        char *f = *(char **)d_008D1244;
        for (i = 0; i < *(int *)(s + 0x1b8); i++) {
            char *c = (*(char ***)(s + 0x1b4))[i];
            if (c != f) {
                ((render_59D310)VT(c)[0xc / 4])(c, dev, elapsed);
                f = *(char **)d_008D1244;
            }
        }
        if (f && *(char **)(f + 0x18) == s)
            ((render_59D310)VT(f)[0xc / 4])(f, dev, elapsed);
    }
    m = *(char **)(sub_00599A20() + 4);
    ((dev0_59D310)VT(m)[0x2c / 4])(m);
    m = *(char **)sub_00599A20();
    ((dev0_59D310)VT(m)[0x14 / 4])(m);
    return 0;
}
