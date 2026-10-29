/* 0x0059CDA0: CDXUTEditBox::Render (device, elapsed; EAX passed through when hidden): when visible (+4) the buffer
 * (+0x54: font node +0x5C, analysis +0x64 rebuilt by 0x00593770 when +0x60 asks, positions by ScriptStringCPtoX through
 * 0x006C828C) takes element 0's font and the caret is placed (0x005956A0); the 9 frame elements (+0x20 list) blend
 * (0x00593EA0, rate 0x0061FCBC) and draw (0x0059A180) in their rects (+0x80); the selection between the caret (+0x11C)
 * and its start (+0x124) is filled (0x00599D50, +0x134), the text from the first visible character (+0x128) drawn in
 * the text colour (+0x12C) in the text rect (+0x70) and the selected part in its colour (+0x130) (0x0059A9E0); the
 * caret (+0x118) blinks every +0x110 seconds of the global timer (0x0059E480, last +0x114) and with the focus (+6),
 * unless hidden (0x008D123C), is drawn in +0x138, one character wide when overwriting (+0x120 clear) */
/* @conv ECX,EAX 8 */
/* @func 0059CDA0 custom */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00599A20(void);
DECOMP_C void __thiscall sub_005956A0(void *self, int pos);
DECOMP_C void __thiscall sub_00593EA0(void *self, int state, float elapsed, float rate);
DECOMP_C void __thiscall sub_0059A180(void *self, void *el, void *rect);
DECOMP_C void __thiscall sub_00599D50(void *self, void *rect, unsigned int color);
DECOMP_C int __thiscall sub_0059A9E0(void *self, const void *text, char *el, const int *rect, unsigned char shadow,
                                     int count);
DECOMP_C int __thiscall sub_00593770(void *self);
DECOMP_C void *__cdecl sub_0059E480(void);
DECOMP_C float __thiscall sub_0059D900(void *timer);
DECOMP_C char d_0061FCBC[], d_006C828C[], d_0060B368[], d_008D123C[];
DECOMP_C int (__stdcall *imp_00607644)(void *, int, int, int, int) __asm__("__imp__SetRect@20");
DECOMP_C int (__stdcall *imp_00607638)(void *, int, int) __asm__("__imp__OffsetRect@12");
DECOMP_C int (__stdcall *imp_0060760C)(void *, const void *, const void *) __asm__("__imp__IntersectRect@16");
typedef int (__stdcall *ssa_cptox_59CDA0)(void *ssa, int cp, int trailing, int *x);

#define ELEM(i) ((*(char ***)(s + 0x20))[i])

static void cptox_59CDA0(char *buf, int cp, int trail, int *x)
{
    *x = 0;
    if (buf[0xc] && sub_00593770(buf) < 0)
        return;
    (*(ssa_cptox_59CDA0 *)d_006C828C)(*(void **)(buf + 0x10), cp, trail, x);
}

static void color_59CDA0(char *s, unsigned int c)
{
    float *f = (float *)(ELEM(0) + 0x5c);
    double k = *(double *)d_0060B368;
    f[0] = (float)((int)((c >> 16) & 0xff) * k);
    f[1] = (float)((int)((c >> 8) & 0xff) * k);
    f[2] = (float)((int)(c & 0xff) * k);
    f[3] = (float)((int)(c >> 24) * k);
}

DECOMP(0059CDA0)
unsigned int __cdecl f_0059CDA0(void *this, unsigned int eax, void *dev, float elapsed)
{
    char *s = (char *)this, *buf = s + 0x54, *el;
    int caretx = 0, selx = 0, first, e, sel[4];
    if (!s[4])
        return eax;
    if (ELEM(0)) {
        char *node;
        int f = *(int *)(ELEM(0) + 4);
        char *dlg = *(char **)(s + 0x18);
        if (!sub_00599A20())
            node = 0;
        else {
            int k = (*(int **)(dlg + 0x1a8))[f];
            node = (*(char ***)(sub_00599A20() + 0x14))[k];
        }
        *(char **)(s + 0x5c) = node;
        sub_005956A0(this, *(int *)(s + 0x11c));
    }
    for (e = 0; e < 9; e++) {
        el = ELEM(e);
        sub_00593EA0(el + 0x1c, 0, elapsed, *(float *)d_0061FCBC);
        sub_0059A180(*(void **)(s + 0x18), el, s + 0x80 + e * 0x10);
    }
    cptox_59CDA0(buf, *(int *)(s + 0x128), 0, &first);
    cptox_59CDA0(buf, *(int *)(s + 0x11c), 0, &caretx);
    if (*(int *)(s + 0x11c) != *(int *)(s + 0x124))
        cptox_59CDA0(buf, *(int *)(s + 0x124), 0, &selx);
    else
        selx = caretx;
    if (*(int *)(s + 0x11c) != *(int *)(s + 0x124)) {
        int l = caretx, r = selx;
        if (l > r) {
            l = selx;
            r = caretx;
        }
        imp_00607644(sel, l, *(int *)(s + 0x74), r, *(int *)(s + 0x7c));
        imp_00607638(sel, *(int *)(s + 0x70) - first, 0);
        imp_0060760C(sel, s + 0x70, sel);
        sub_00599D50(*(void **)(s + 0x18), sel, *(unsigned int *)(s + 0x134));
    }
    color_59CDA0(s, *(unsigned int *)(s + 0x12c));
    sub_0059A9E0(*(void **)(s + 0x18), *(short **)buf + *(int *)(s + 0x128), ELEM(0), (int *)(s + 0x70), 0, -1);
    if (*(int *)(s + 0x11c) != *(int *)(s + 0x124)) {
        int *pmin = *(int *)(s + 0x11c) < *(int *)(s + 0x124) ? (int *)(s + 0x11c) : (int *)(s + 0x124);
        int *pfirst = *(int *)(s + 0x128) < *pmin ? pmin : (int *)(s + 0x128);
        int nfirst = *pfirst;
        int *pmax = *(int *)(s + 0x124) < *(int *)(s + 0x11c) ? (int *)(s + 0x11c) : (int *)(s + 0x124);
        int cnt = *pmax - nfirst;
        color_59CDA0(s, *(unsigned int *)(s + 0x130));
        sub_0059A9E0(*(void **)(s + 0x18), *(short **)buf + nfirst, ELEM(0), sel, 0, cnt);
    }
    if (sub_0059D900(sub_0059E480()) - *(float *)(s + 0x114) >= *(float *)(s + 0x110)) {
        s[0x118] = !s[0x118];
        *(float *)(s + 0x114) = sub_0059D900(sub_0059E480());
    }
    if (s[6] && s[0x118] && !*d_008D123C) {
        int rc[4], x = *(int *)(s + 0x70) - first + caretx;
        rc[0] = x - 1;
        rc[1] = *(int *)(s + 0x74);
        rc[2] = x + 1;
        rc[3] = *(int *)(s + 0x7c);
        if (!s[0x120]) {
            int right;
            cptox_59CDA0(buf, *(int *)(s + 0x11c), 1, &right);
            rc[2] = *(int *)(s + 0x70) - first + right;
        }
        sub_00599D50(*(void **)(s + 0x18), rc, *(unsigned int *)(s + 0x138));
    }
    return 0;
}
