/* 0x00592F10: CDXUTButton::HandleMouse (vf6): enabled (+0x3C) and visible (+4): a left press or double click on it
 * (vf34 ContainsPoint) presses it (+0x158), captures the mouse and asks the dialog (+0x18) for the focus
 * (0x00592DA0) unless it has it (+6); a left release of a pressed button releases the capture, the focus when the
 * dialog does not keep it (+0x59, 0x00592E40), and on the button sends EVENT_BUTTON_CLICKED (0x101) with its ID
 * (+0x2C) to the dialog's callback (+0x198); a bool in AL */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00592DA0(unsigned int eax, void *control);
DECOMP_C int __cdecl sub_00592E40(void);
DECOMP_C char d_006C889C[];
DECOMP_C void *(__stdcall *imp_00607640)(void *) __asm__("__imp__SetCapture@4");
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
typedef int (__thiscall *vf34_592F10)(void *self, int x, int y);
typedef void (__stdcall *event_592F10)(unsigned int ev, int id, void *control);

DECOMP(00592F10)
unsigned char __thiscall f_00592F10(void *this, unsigned int msg, int x, int y, unsigned int wparam, unsigned int lparam)
{
    unsigned char *s = (unsigned char *)this;
    if (!s[0x3c] || !s[4])
        return 0;
    if (msg == 0x201 || msg == 0x203) {             /* WM_LBUTTONDOWN, WM_LBUTTONDBLCLK */
        unsigned int prev;
        if (!((vf34_592F10)(*(void ***)this)[0x34 / 4])(this, x, y))
            return 0;
        s[0x158] = 1;
        prev = (unsigned int)imp_00607640(*(void **)d_006C889C);
        if (!s[6])
            sub_00592DA0(prev, this);
        return 1;
    }
    if (msg != 0x202 || !s[0x158])                  /* WM_LBUTTONUP */
        return 0;
    s[0x158] = 0;
    imp_00607648();
    if (!(*(unsigned char **)(s + 0x18))[0x59])
        sub_00592E40();
    if (((vf34_592F10)(*(void ***)this)[0x34 / 4])(this, x, y)) {
        event_592F10 cb = *(event_592F10 *)(*(char **)(s + 0x18) + 0x198);
        if (cb)
            cb(0x101, *(int *)(s + 0x2c), this);
    }
    return 1;
}
