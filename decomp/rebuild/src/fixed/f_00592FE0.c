/* 0x00592FE0: CDXUTCheckBox::HandleKeyboard (vf5): enabled (+0x3C) and visible (+4): space down presses (+0x158),
 * space up toggles the check (+0x15C, vf50 SetCheckedInternal(!checked, from input)) if pressed; true when handled
 * (a bool in AL) */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef void (__thiscall *vf50_592FE0)(void *self, int checked, int from_input);

DECOMP(00592FE0)
unsigned char __thiscall f_00592FE0(void *this, unsigned int msg, unsigned int wparam, unsigned int lparam)
{
    unsigned char *s = (unsigned char *)this;
    if (!s[0x3c] || !s[4])
        return 0;
    if (msg == 0x100) {                     /* WM_KEYDOWN */
        if (wparam != 0x20)                 /* VK_SPACE */
            return 0;
        s[0x158] = 1;
        return 1;
    }
    if (msg != 0x101 || wparam != 0x20)     /* WM_KEYUP */
        return 0;
    if (s[0x158] == 1) {
        s[0x158] = 0;
        ((vf50_592FE0)(*(void ***)this)[0x50 / 4])(this, s[0x15c] == 0, 1);
    }
    return 1;
}
