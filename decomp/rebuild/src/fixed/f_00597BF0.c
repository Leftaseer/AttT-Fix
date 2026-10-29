/* 0x00597BF0: CDXUTListBox::HandleMouse (vf6): enabled (+0x3C) and visible (+4); a left press takes the focus
 * (0x00592DA0, unless +6) and the scroll bar (+0x74, vf18) goes first. A press or double click on an item in the
 * selection rect (+0x64; rows of +0x138 from the text top +0x58, from the scroll position +0x10C within the page
 * +0x110) captures the mouse and starts a drag (+0x148); a double click sends EVENT_LISTBOX_ITEM_DBLCLK (0x701), a
 * press selects (+0x140, the anchor +0x144 unless Shift) and, for a multi-selection list (+0x13C bit 0), toggles
 * (Ctrl), selects the range (Shift), extends the anchor's state (both) or selects only that item (+0x14C items,
 * selected +0x114), sending EVENT_LISTBOX_SELECTION (0x702). A release ends the drag and gives the range the anchor's
 * state (0x702 when it moved); a drag selects the item under the cursor, scrolling (0x005951F0) past the edges; the
 * wheel scrolls by the system's lines. Events go to the dialog's (+0x18) callback (+0x198) with the ID (+0x2C). A bool
 * in AL, the rest of EAX as the original leaves it when hidden */
/* @conv ECX,EAX 20 */
/* @func 00597BF0 custom */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_00592DA0(unsigned int eax, void *control);
DECOMP_C void __thiscall sub_005951F0(void *self, int delta);
DECOMP_C char d_006C889C[];
DECOMP_C void *(__stdcall *imp_00607640)(void *) __asm__("__imp__SetCapture@4");
DECOMP_C int (__stdcall *imp_00607648)(void) __asm__("__imp__ReleaseCapture@0");
DECOMP_C int (__stdcall *imp_0060763C)(const void *, int, int) __asm__("__imp__PtInRect@12");
DECOMP_C int (__stdcall *imp_00607614)(unsigned int, unsigned int, void *, unsigned int) __asm__("__imp__SystemParametersInfoA@16");
typedef char (__thiscall *mouse_597BF0)(void *self, unsigned int msg, int x, int y, unsigned int wp, unsigned int lp);
typedef void (__stdcall *event_597BF0)(unsigned int ev, int id, void *control);

#define ITEM(i) ((*(unsigned char ***)(s + 0x14c))[i])
#define COUNT (*(int *)(s + 0x150))
#define TRACK (*(int *)(s + 0x10c))
#define PAGE (*(int *)(s + 0x110))
#define SEL (*(int *)(s + 0x140))
#define START (*(int *)(s + 0x144))

static void send_597BF0(unsigned char *s, unsigned int ev)
{
    event_597BF0 cb = *(event_597BF0 *)(*(char **)(s + 0x18) + 0x198);
    if (cb)
        cb(ev, *(int *)(s + 0x2c), s);
}

static int row_597BF0(unsigned char *s, int y)
{
    int h = *(int *)(s + 0x138);
    return h ? (y - *(int *)(s + 0x58)) / h + TRACK : -1;
}

DECOMP(00597BF0)
unsigned int __cdecl f_00597BF0(void *this, unsigned int eax, unsigned int msg, int x, int y, unsigned int wp,
                                unsigned int lp)
{
    unsigned char *s = (unsigned char *)this;
    int i, n;
    if (!s[0x3c] || !s[4])
        return eax & 0xffffff00;
    if (msg == 0x201 && !s[6])
        sub_00592DA0(eax, this);
    if (((mouse_597BF0)(*(void ***)(s + 0x74))[0x18 / 4])(s + 0x74, msg, x, y, wp, lp))
        return 1;
    switch (msg) {
    case 0x201:                                     /* WM_LBUTTONDOWN, WM_LBUTTONDBLCLK */
    case 0x203: {
        unsigned char *p;
        if (COUNT <= 0 || !imp_0060763C(s + 0x64, x, y))
            return 0;
        n = row_597BF0(s, y);
        if (n < TRACK || n >= COUNT || n >= TRACK + PAGE)
            return 1;
        imp_00607640(*(void **)d_006C889C);
        s[0x148] = 1;
        if (msg == 0x203) {
            send_597BF0(s, 0x701);
            return 1;
        }
        SEL = n;
        if (!(wp & 4))
            START = n;
        if (*(unsigned int *)(s + 0x13c) & 1) {
            int lo = SEL < START ? SEL : START, hi = START < SEL ? SEL : START;
            p = ITEM(n);
            switch (wp & 0xc) {
            case 8:                                 /* Ctrl */
                p[0x114] = !p[0x114];
                break;
            case 4:                                 /* Shift */
                for (i = 0; i < lo; i++)
                    ITEM(i)[0x114] = 0;
                for (i = hi + 1; i < COUNT; i++)
                    ITEM(i)[0x114] = 0;
                for (i = lo; i <= hi; i++)
                    ITEM(i)[0x114] = 1;
                break;
            case 0xc: {
                unsigned char st = ITEM(START)[0x114];
                for (i = lo + 1; i < hi; i++)
                    ITEM(i)[0x114] = st;
                p[0x114] = 1;
                SEL = START;
                break;
            }
            default:
                for (i = 0; i < COUNT; i++)
                    ITEM(i)[0x114] = 0;
                p[0x114] = 1;
            }
        }
        send_597BF0(s, 0x702);
        return 1;
    }
    case 0x202:                                     /* WM_LBUTTONUP */
        imp_00607648();
        s[0x148] = 0;
        if (SEL != -1) {
            int hi = START < SEL ? SEL : START, lo = SEL < START ? SEL : START;
            for (i = lo + 1; i < hi; i++)
                ITEM(i)[0x114] = ITEM(START)[0x114];
            ITEM(SEL)[0x114] = ITEM(START)[0x114];
            if (START != SEL)
                send_597BF0(s, 0x702);
        }
        return 0;
    case 0x200:                                     /* WM_MOUSEMOVE */
        if (!s[0x148])
            return 0;
        n = row_597BF0(s, y);
        if (n >= TRACK && n < COUNT && n < TRACK + PAGE)
            SEL = n;
        else if (n < TRACK) {
            sub_005951F0(s + 0x74, -1);
            SEL = TRACK;
        } else if (n >= TRACK + PAGE) {
            int last;
            sub_005951F0(s + 0x74, 1);
            last = PAGE + TRACK;
            SEL = (last < COUNT ? last : COUNT) - 1;
        } else
            return 0;
        send_597BF0(s, 0x702);
        return 0;
    case 0x20a: {                                   /* WM_MOUSEWHEEL */
        unsigned int lines;
        imp_00607614(0x68, 0, &lines, 0);           /* SPI_GETWHEELSCROLLLINES */
        sub_005951F0(s + 0x74, -((short)(wp >> 16) / 120) * (int)lines);
        return 1;
    }
    }
    return 0;
}
