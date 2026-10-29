/* 0x00596820: CDXUTDialog::MsgProc (window, message, wParam, lParam): the console key (scan code 0x29) is left to the
 * game; a hidden dialog (+0x70) handles nothing. With a caption (+0x71) a left press in it starts a drag (0x008D1259,
 * SetCapture) and a release there toggles minimized (+0x72), telling the focused control (0x008D1244) of this dialog
 * (+0x18) that is enabled (vf3C) it lost or regained the focus (vf24 / vf20). Minimized: nothing more. The focused
 * control gets each message first (vf10); WM_ACTIVATEAPP refocuses or unfocuses it; key messages go to its keyboard
 * handler (vf14), a key down then matches control hotkeys (+0x34, vf30 unless an edit box has the focus, types 6/7)
 * and, with keyboard input (+0x59), arrows / Tab cycle the focus (0x00594780, EAX the key's case; Tab without a focus
 * focuses the default control 0x00594720); mouse messages with mouse input (+0x5A) go, relative to the dialog
 * (+0x174 / +0x178, below the caption +0x184), to the focused control then the control under the cursor (0x005944D0,
 * vf18), a press elsewhere drops the focus, and a move is tracked (0x00594540) and handled when inside the dialog
 * (+0x17C x +0x180). A bool in AL */
/* @conv ECX,EAX 16 */
/* @func 00596820 custom */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00594780(void *self, unsigned int eax, char forward);
DECOMP_C void __thiscall sub_00594720(void *self);
DECOMP_C char *__thiscall sub_005944D0(void *self, int x, int y);
DECOMP_C void __thiscall sub_00594540(void *self, int x, int y);
DECOMP_C char d_008D1259[], d_008D1244[], d_006C889C[];
DECOMP_C void *(__stdcall *imp_00607640)(void *) __asm__("__imp__SetCapture@4");
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
DECOMP_C short (__stdcall *imp_00607618)(int) __asm__("__imp__GetAsyncKeyState@4");
typedef char (__thiscall *vf0_596820)(void *self);
typedef char (__thiscall *msg_596820)(void *self, unsigned int msg, unsigned int wp, unsigned int lp);
typedef char (__thiscall *mouse_596820)(void *self, unsigned int msg, int x, int y, unsigned int wp, unsigned int lp);

#define VT(o) (*(void ***)(o))
#define FOCUS (*(char **)d_008D1244)
#define DRAG (*(unsigned char *)d_008D1259)
#define I(o) (*(int *)(s + (o)))

static int ours_596820(char *s, char *f)
{
    return f && *(char **)(f + 0x18) == s && ((vf0_596820)VT(f)[0x3c / 4])(f);
}

static int incaption_596820(char *s, unsigned int lp)
{
    int x = (short)lp, y = (short)(lp >> 16);
    return x >= I(0x174) && x < I(0x174) + I(0x17c) && y >= I(0x178) && y < I(0x178) + I(0x184);
}

DECOMP(00596820)
unsigned int __cdecl f_00596820(void *this, unsigned int eax, void *hwnd, unsigned int msg, unsigned int wp,
                                unsigned int lp)
{
    char *s = (char *)this, *f;
    int i;
    if ((msg == 0x100 || msg == 0x102) && (lp & 0xff0000) == 0x290000)
        return 0;
    if (!s[0x70])
        return 0;
    if (s[0x71]) {
        if (msg == 0x201 || msg == 0x203) {
            if (incaption_596820(s, lp)) {
                DRAG = 1;
                imp_00607640(*(void **)d_006C889C);
                return 1;
            }
        } else if (msg == 0x202 && DRAG && incaption_596820(s, lp)) {
            imp_00607648();
            DRAG = 0;
            s[0x72] = !s[0x72];
            f = FOCUS;
            if (ours_596820(s, f)) {
                f = FOCUS;
                ((vf0_596820)VT(f)[(s[0x72] ? 0x24 : 0x20) / 4])(f);
            }
            return 1;
        }
    }
    if (s[0x72])
        return 0;
    f = FOCUS;
    if (ours_596820(s, f) && ((msg_596820)VT(FOCUS)[0x10 / 4])(FOCUS, msg, wp, lp))
        return 1;
    f = FOCUS;
    if (msg == 0x1c) {                              /* WM_ACTIVATEAPP */
        if (ours_596820(s, f))
            ((vf0_596820)VT(FOCUS)[(wp ? 0x20 : 0x24) / 4])(FOCUS);
        return 0;
    }
    if ((msg >= 0x100 && msg <= 0x101) || msg == 0x104 || msg == 0x105) {
        if (ours_596820(s, f) && ((msg_596820)VT(FOCUS)[0x14 / 4])(FOCUS, msg, wp, lp))
            return 1;
        f = FOCUS;
        if (msg != 0x100)
            return 0;
        if (!f || (*(int *)(f + 0x30) != 6 && *(int *)(f + 0x30) != 7))
            for (i = 0; i < I(0x1b8); i++) {
                char *c = (*(char ***)(s + 0x1b4))[i];
                if (*(unsigned int *)(c + 0x34) == wp) {
                    ((vf0_596820)VT(c)[0x30 / 4])(c);
                    return 1;
                }
            }
        if (!s[0x59])
            return 0;
        switch (wp) {
        case 9:                                     /* VK_TAB */
            if (!f) {
                sub_00594720(this);
                return 1;
            } else {
                unsigned int k = ((unsigned short)imp_00607618(0x10) >> 15) & 1;
                sub_00594780(this, k, !k);
                return 1;
            }
        case 0x25:                                  /* VK_LEFT, VK_UP */
        case 0x26:
            if (!f)
                return 0;
            sub_00594780(this, 1, 0);
            return 1;
        case 0x27:                                  /* VK_RIGHT, VK_DOWN */
        case 0x28:
            if (!f)
                return 0;
            sub_00594780(this, 2, 1);
            return 1;
        }
        return 0;
    }
    if (msg >= 0x200 && msg <= 0x20d) {
        int x, y;
        char *c;
        if (!s[0x5a])
            return 0;
        x = (short)lp - I(0x174);
        y = (short)(lp >> 16) - I(0x178);
        if (s[0x71])
            y -= I(0x184);
        if (ours_596820(s, f) && ((mouse_596820)VT(FOCUS)[0x18 / 4])(FOCUS, msg, x, y, wp, lp))
            return 1;
        c = sub_005944D0(this, x, y);
        if (c && ((vf0_596820)VT(c)[0x3c / 4])(c)) {
            if (((mouse_596820)VT(c)[0x18 / 4])(c, msg, x, y, wp, lp))
                return 1;
        } else if (msg == 0x201) {
            f = FOCUS;
            if (f && *(char **)(f + 0x18) == s) {
                ((vf0_596820)VT(f)[0x24 / 4])(f);
                FOCUS = 0;
            }
            return 0;
        }
        if (msg != 0x200)
            return 0;
        sub_00594540(this, x, y);
        return x >= 0 && y >= 0 && x <= I(0x17c) && y <= I(0x180);
    }
    return 0;
}
