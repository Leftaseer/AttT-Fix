/* 0x00596F10: CDXUTComboBox::HandleMouse (vf6): enabled (+0x3C) and visible (+4), after its scroll bar (+0x168, vf18):
 * a move over the open (+0x224) drop-down (+0x248) focuses the visible item (+0x268 / +0x26C: rect +0x104, shown +0x114)
 * under it (+0x160); a left press or double click on the box (vf34) presses it (+0x158), captures the mouse, takes the
 * focus (0x00592DA0, unless +6) and toggles the drop-down (closing drops the focus unless the dialog (+0x18) keeps it,
 * +0x59, 0x00592E40); one in the open drop-down selects the item under it from the scroll position (+0x200: selected
 * +0x15C and focused) and closes it; one elsewhere closes it back on the selection and releases; a release of the
 * pressed box releases the capture; the wheel scrolls the open list by the system's lines (0x005951F0) or steps the
 * selection. Changes go to the dialog's callback (+0x198) as EVENT_COMBOBOX_SELECTION_CHANGED (0x201) with the ID
 * (+0x2C). A bool in AL, the rest of EAX as the original leaves it when it is not shown */
/* @conv ECX,EAX 20 */
/* @func 00596F10 custom */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00592DA0(unsigned int eax, void *control);
DECOMP_C int __cdecl sub_00592E40(void);
DECOMP_C void __thiscall sub_005951F0(void *self, int delta);
DECOMP_C char d_006C889C[];
DECOMP_C void *(__stdcall *imp_00607640)(void *) __asm__("__imp__SetCapture@4");
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
DECOMP_C int (__stdcall *imp_0060763C)(const void *, int, int) __asm__("__imp__PtInRect@12");
DECOMP_C int (__stdcall *imp_00607614)(unsigned int, unsigned int, void *, unsigned int) __asm__("__imp__SystemParametersInfoA@16");
typedef char (__thiscall *mouse_596F10)(void *self, unsigned int msg, int x, int y, unsigned int wp, unsigned int lp);
typedef int (__thiscall *vf34_596F10)(void *self, int x, int y);
typedef void (__stdcall *event_596F10)(unsigned int ev, int id, void *control);

#define ITEM(i) ((*(unsigned char ***)(s + 0x268))[i])
#define NITEMS (*(int *)(s + 0x26c))
#define DLG (*(unsigned char **)(s + 0x18))

static void changed_596F10(unsigned char *s)
{
    event_596F10 cb = *(event_596F10 *)(DLG + 0x198);
    if (cb)
        cb(0x201, *(int *)(s + 0x2c), s);
}

DECOMP(00596F10)
unsigned int __cdecl f_00596F10(void *this, unsigned int eax, unsigned int msg, int x, int y, unsigned int wp,
                                unsigned int lp)
{
    unsigned char *s = (unsigned char *)this;
    int i;
    if (!s[0x3c] || !s[4])
        return eax & 0xffffff00;
    if (((mouse_596F10)(*(void ***)(s + 0x168))[0x18 / 4])(s + 0x168, msg, x, y, wp, lp))
        return 1;
    switch (msg) {
    case 0x200:                                     /* WM_MOUSEMOVE */
        if (!s[0x224] || !imp_0060763C(s + 0x248, x, y))
            return 0;
        for (i = 0; i < NITEMS; i++)
            if (ITEM(i)[0x114] && imp_0060763C(ITEM(i) + 0x104, x, y))
                *(int *)(s + 0x160) = i;
        return 1;
    case 0x201:                                     /* WM_LBUTTONDOWN, WM_LBUTTONDBLCLK */
    case 0x203:
        if (((vf34_596F10)(*(void ***)this)[0x34 / 4])(this, x, y)) {
            unsigned int prev;
            s[0x158] = 1;
            prev = (unsigned int)imp_00607640(*(void **)d_006C889C);
            if (!s[6]) {
                sub_00592DA0(prev, this);
                if (!s[6])
                    return 1;
            }
            s[0x224] = !s[0x224];
            if (!s[0x224] && !DLG[0x59])
                sub_00592E40();
            return 1;
        }
        if (s[0x224]) {
            if (imp_0060763C(s + 0x248, x, y)) {
                for (i = *(int *)(s + 0x200); i < NITEMS; i++)
                    if (ITEM(i)[0x114] && imp_0060763C(ITEM(i) + 0x104, x, y)) {
                        *(int *)(s + 0x15c) = i;
                        *(int *)(s + 0x160) = i;
                        changed_596F10(s);
                        s[0x224] = 0;
                        if (!DLG[0x59])
                            sub_00592E40();
                        break;
                    }
                return 1;
            }
            *(int *)(s + 0x160) = *(int *)(s + 0x15c);
            changed_596F10(s);
            s[0x224] = 0;
        }
        s[0x158] = 0;
        if (!DLG[0x59])
            sub_00592E40();
        return 0;
    case 0x202:                                     /* WM_LBUTTONUP */
        if (!s[0x158] || !((vf34_596F10)(*(void ***)this)[0x34 / 4])(this, x, y))
            return 0;
        s[0x158] = 0;
        imp_00607648();
        return 1;
    case 0x20a: {                                   /* WM_MOUSEWHEEL */
        int z = (short)(wp >> 16) / 120;
        if (s[0x224]) {
            unsigned int lines;
            imp_00607614(0x68, 0, &lines, 0);       /* SPI_GETWHEELSCROLLLINES */
            sub_005951F0(s + 0x168, -(int)(lines * z));
            return 1;
        }
        i = *(int *)(s + 0x160);
        if (z > 0) {
            if (i > 0) {
                *(int *)(s + 0x160) = i - 1;
                *(int *)(s + 0x15c) = i - 1;
                changed_596F10(s);
            }
        } else if (i + 1 < NITEMS) {
            *(int *)(s + 0x160) = i + 1;
            *(int *)(s + 0x15c) = i + 1;
            changed_596F10(s);
        }
        return 1;
    }
    }
    return 0;
}
