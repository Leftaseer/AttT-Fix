/* 0x00595F60: an edit box's WM_CHAR handler (visible +0x3C and enabled +0x04; anything else returns false with EAX's
 * upper bytes as they came): Ctrl+A selects all (cursor +0x11C to the end, the anchor +0x124 to 0, when nothing is
 * selected); Ctrl+C copies (0x00595970) and Ctrl+X also deletes the selection (0x00595850); backspace deletes the
 * selection or the character before the cursor (0x005956A0, 0x00593A90 on the text +0x54); Enter notifies the
 * owner (+0x18's +0x198 callback, 0x601) and restores the focus (0x00592E40); Ctrl+V pastes (0x00595A40); other
 * control characters are ignored; a character replaces the selection, then overwrites (unless inserting, +0x120,
 * or at the end; +0x60 marks the change) or is inserted (0x00593A00, its EAX input only passed through); changes
 * notify the owner (0x602) and refresh (0x00593DE0). True when handled */
/* @conv ECX,EAX 12 */
/* @func 00595F60 custom */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00595850(void *self);
DECOMP_C int __thiscall sub_00593DE0(void *self);
DECOMP_C void __thiscall sub_005956A0(void *self, int pos);
DECOMP_C void __thiscall sub_00593A90(void *self, int pos);
DECOMP_C void __thiscall sub_00595970(void *self);
DECOMP_C void __thiscall sub_00595A40(void *self);
DECOMP_C void __cdecl sub_00592E40(void);
DECOMP_C unsigned int __cdecl sub_00593A00(void *self, unsigned int eax, int pos, unsigned int ch);
DECOMP_C int (__stdcall *imp_00607070)(const unsigned short *) __asm__("__imp__lstrlenW@4");
typedef void (__stdcall *cb_595F60)(unsigned int code, unsigned int id, void *ctl);

static void notify_595F60(char *s, unsigned int code)
{
    cb_595F60 cb = *(cb_595F60 *)(*(char **)(s + 0x18) + 0x198);
    if (cb)
        cb(code, *(unsigned int *)(s + 0x2c), s);
}

#define CUR (*(int *)(s + 0x11c))
#define ANCHOR (*(int *)(s + 0x124))
#define TEXT (*(unsigned short **)(s + 0x54))

DECOMP(00595F60)
unsigned int __cdecl f_00595F60(void *this, unsigned int eax, unsigned int msg, unsigned int wp, unsigned int lp)
{
    char *s = (char *)this;
    unsigned short c = (unsigned short)wp;
    if (!s[0x3c] || !s[4] || msg != 0x102)
        return eax & ~0xffu;
    switch (c) {
    case 1:
        if (ANCHOR == CUR) {
            ANCHOR = 0;
            sub_005956A0(this, imp_00607070(TEXT));
        }
        return 1;
    case 3:
    case 0x18:
        sub_00595970(this);
        if (c == 0x18) {
            sub_00595850(this);
            notify_595F60(s, 0x602);
        }
        return 1;
    case 8:
        if (CUR != ANCHOR) {
            sub_00595850(this);
            notify_595F60(s, 0x602);
        } else if (CUR > 0) {
            sub_005956A0(this, CUR - 1);
            ANCHOR = CUR;
            sub_00593A90(s + 0x54, CUR);
            notify_595F60(s, 0x602);
        }
        sub_00593DE0(this);
        return 1;
    case 0xd:
        notify_595F60(s, 0x601);
        sub_00592E40();
        return 1;
    case 0x16:
        sub_00595A40(this);
        notify_595F60(s, 0x602);
        return 1;
    default:
        if (c >= 1 && c <= 0x1d)
            return 1;
        break;
    }
    if (CUR != ANCHOR)
        sub_00595850(this);
    if (!s[0x120] && CUR < imp_00607070(TEXT)) {
        s[0x60] = 1;
        TEXT[CUR] = c;
    } else if (!(char)sub_00593A00(s + 0x54, 0, CUR, wp)) {
        sub_00593DE0(this);
        notify_595F60(s, 0x602);
        return 1;
    }
    sub_005956A0(this, CUR + 1);
    ANCHOR = CUR;
    sub_00593DE0(this);
    notify_595F60(s, 0x602);
    return 1;
}
