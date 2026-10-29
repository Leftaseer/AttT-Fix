/* 0x00595AC0: an edit box's WM_KEYDOWN handler (visible +0x3C and enabled +0x04): Home / End move the cursor (+0x11C,
 * 0x005956A0) to the start / end, left / right by a character or with Ctrl by a word (0x00593C80 / 0x00593D10 on the
 * text +0x54), the selection anchor (+0x124) following unless Shift is held; Delete removes the selection
 * (0x00595850) or the character at the cursor (0x00593A90), notifying the owner (+0x18's +0x198 callback, 0x602);
 * moves refresh (0x00593DE0). Insert copies with Ctrl (0x00595970), pastes with Shift (0x00595A40) or toggles insert
 * mode (+0x120), reporting the key unhandled; up / down are swallowed; other keys are handled unless Escape */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_005956A0(void *self, int pos);
DECOMP_C int __thiscall sub_00593DE0(void *self);
DECOMP_C void __thiscall sub_00595970(void *self);
DECOMP_C void __thiscall sub_00595A40(void *self);
DECOMP_C void __thiscall sub_00595850(void *self);
DECOMP_C char __thiscall sub_00593A90(void *self, int pos);
DECOMP_C void __thiscall sub_00593C80(void *self, int pos, int *out);
DECOMP_C void __thiscall sub_00593D10(void *self, int pos, int *out);
DECOMP_C int (__stdcall *imp_00607070)(const unsigned short *) __asm__("__imp__lstrlenW@4");
DECOMP_C short (__stdcall *imp_006076D0)(int) __asm__("__imp__GetKeyState@4");
typedef void (__stdcall *cb_595AC0)(unsigned int code, unsigned int id, void *ctl);

#define CUR (*(int *)(s + 0x11c))
#define ANCHOR (*(int *)(s + 0x124))
#define TEXT (*(unsigned short **)(s + 0x54))

static unsigned char moved_595AC0(char *s)
{
    if (imp_006076D0(0x10) >= 0)
        ANCHOR = CUR;
    sub_00593DE0(s);
    return 1;
}

DECOMP(00595AC0)
unsigned char __thiscall f_00595AC0(void *this, unsigned int msg, unsigned int wp, unsigned int lp)
{
    char *s = (char *)this;
    cb_595AC0 cb;
    if (!s[0x3c] || !s[4])
        return 0;
    if (msg != 0x100)
        return 0;
    switch (wp) {
    case 0x24:
        sub_005956A0(this, 0);
        return moved_595AC0(s);
    case 0x23:
        sub_005956A0(this, imp_00607070(TEXT));
        return moved_595AC0(s);
    case 0x2d:
        if (imp_006076D0(0x11) < 0)
            sub_00595970(this);
        else if (imp_006076D0(0x10) < 0)
            sub_00595A40(this);
        else
            s[0x120] = !s[0x120];
        return 0;
    case 0x2e:
        if (CUR != ANCHOR) {
            sub_00595850(this);
            cb = *(cb_595AC0 *)(*(char **)(s + 0x18) + 0x198);
            if (cb)
                cb(0x602, *(unsigned int *)(s + 0x2c), s);
        } else if (sub_00593A90(s + 0x54, CUR)) {
            cb = *(cb_595AC0 *)(*(char **)(s + 0x18) + 0x198);
            if (cb)
                cb(0x602, *(unsigned int *)(s + 0x2c), s);
        }
        sub_00593DE0(this);
        return 1;
    case 0x25:
        if (imp_006076D0(0x11) < 0) {
            sub_00593C80(s + 0x54, CUR, &CUR);
            sub_005956A0(this, CUR);
        } else if (CUR > 0)
            sub_005956A0(this, CUR - 1);
        return moved_595AC0(s);
    case 0x27:
        if (imp_006076D0(0x11) < 0) {
            sub_00593D10(s + 0x54, CUR, &CUR);
            sub_005956A0(this, CUR);
        } else if (CUR < imp_00607070(TEXT))
            sub_005956A0(this, CUR + 1);
        return moved_595AC0(s);
    case 0x26:
    case 0x28:
        return 1;
    default:
        return wp != 0x1b;
    }
}
