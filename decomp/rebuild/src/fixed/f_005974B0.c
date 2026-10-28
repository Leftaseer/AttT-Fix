/* 0x005974B0: CDXUTSlider::HandleMouse (vf6): enabled (+0x3C) and visible (+4): dragging (+0x6C) moves the value to
 * the mouse (ValueFromPos 0x00593340 of x + the drag offset +0x64 + the slider's x +8; SetValueInternal 0x005950E0);
 * a press on the thumb (+0x70) starts the drag (capture, +0x60, +0x64, focus 0x00592DA0), on the track (+0x40) steps
 * the value toward the mouse; the release ends it and sends EVENT_SLIDER_VALUE_CHANGED (0x501) with its ID (+0x2C) to
 * the dialog's callback (+0x198); a bool in AL */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00593340(void *self, int x);
DECOMP_C void __thiscall sub_005950E0(void *self, int value, int from_input);
DECOMP_C unsigned int __cdecl sub_00592DA0(unsigned int eax, void *control);
DECOMP_C char d_006C889C[];
DECOMP_C int (__stdcall *imp_0060763C)(const void *, int, int) __asm__("__imp__PtInRect@12");
DECOMP_C void *(__stdcall *imp_00607640)(void *) __asm__("__imp__SetCapture@4");
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
typedef void (__stdcall *event_5974B0)(unsigned int ev, int id, void *control);

DECOMP(005974B0)
unsigned char __thiscall f_005974B0(void *this, unsigned int msg, int x, int y, unsigned int wparam, unsigned int lparam)
{
    char *s = (char *)this;
    int *f = (int *)this;
    if (!s[0x3c] || !s[4])
        return 0;
    switch (msg - 0x200) {
    case 0:                                             /* WM_MOUSEMOVE */
        if (!s[0x6c])
            return 0;
        sub_005950E0(this, sub_00593340(this, f[0x64 / 4] + f[2] + x), 1);
        return 1;
    case 1: case 3: {                                   /* WM_LBUTTONDOWN, WM_LBUTTONDBLCLK */
        unsigned int r;
        if (imp_0060763C(s + 0x70, x, y)) {
            s[0x6c] = 1;
            r = (unsigned int)imp_00607640(*(void **)d_006C889C);
            f[0x60 / 4] = x;
            f[0x64 / 4] = f[0x68 / 4] - x;
            if (!s[6])
                sub_00592DA0(r, this);
            return 1;
        }
        r = imp_0060763C(s + 0x40, x, y);
        if (!r)
            return 0;
        f[0x60 / 4] = x;
        f[0x64 / 4] = 0;
        s[0x6c] = 1;
        if (!s[6])
            sub_00592DA0(r, this);
        if (x > f[0x68 / 4] + f[2]) {
            sub_005950E0(this, f[0x54 / 4] + 1, 1);
            return 1;
        }
        if (x < f[0x68 / 4] + f[2]) {
            sub_005950E0(this, f[0x54 / 4] - 1, 1);
            return 1;
        }
        return 0;
    }
    case 2: {                                           /* WM_LBUTTONUP */
        event_5974B0 cb;
        if (!s[0x6c])
            return 0;
        s[0x6c] = 0;
        imp_00607648();
        cb = *(event_5974B0 *)(*(char **)(s + 0x18) + 0x198);
        if (cb)
            cb(0x501, f[0x2c / 4], this);
        return 1;
    }
    }
    return 0;
}
