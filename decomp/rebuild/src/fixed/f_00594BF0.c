/* 0x00594BF0: a drop-down list's message handler (msg, wParam, lParam), while visible (+0x3C) and enabled (+0x04):
 * its part +0x168 (vf14) first; then key presses (WM_KEYDOWN): Enter closes an open list (+0x224), selecting the
 * highlighted item (+0x160 into +0x15C) with the owner's (+0x18) callback (+0x198: 0x201, the id +0x2C, this); F4
 * (not repeated) opens or closes it (closing calls back); left / up and right / down move the selection within the
 * +0x26C items, calling back while closed. Closing restores the focus (0x00592E40) unless the owner's +0x59 is set.
 * True when handled */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00592E40(void);
typedef char (__thiscall *msg_594BF0)(void *self, unsigned int msg, unsigned int wp, unsigned int lp);
typedef void (__stdcall *cb_594BF0)(unsigned int code, unsigned int id, void *ctl);

static void notify_594BF0(char *s)
{
    cb_594BF0 cb = *(cb_594BF0 *)(*(char **)(s + 0x18) + 0x198);
    if (cb)
        cb(0x201, *(unsigned int *)(s + 0x2c), s);
}

static unsigned char closed_594BF0(char *s)
{
    if (!(*(char **)(s + 0x18))[0x59])
        sub_00592E40();
    return 1;
}

DECOMP(00594BF0)
unsigned char __thiscall f_00594BF0(void *this, unsigned int msg, unsigned int wp, unsigned int lp)
{
    char *s = (char *)this;
    void **part = (void **)(s + 0x168);
    int v;
    if (!s[0x3c] || !s[4])
        return 0;
    if (((msg_594BF0)(*(void ***)part)[0x14 / 4])(part, msg, wp, lp))
        return 1;
    if (msg != 0x100)
        return 0;
    switch (wp) {
    case 0xd:
        if (!s[0x224])
            return 0;
        if (*(int *)(s + 0x15c) != *(int *)(s + 0x160)) {
            *(int *)(s + 0x15c) = *(int *)(s + 0x160);
            notify_594BF0(s);
        }
        s[0x224] = 0;
        return closed_594BF0(s);
    case 0x73:
        if (lp & 0x40000000)
            return 1;
        s[0x224] = !s[0x224];
        if (s[0x224])
            return 1;
        notify_594BF0(s);
        return closed_594BF0(s);
    case 0x25:
    case 0x26:
        v = *(int *)(s + 0x160);
        if (v <= 0)
            return 1;
        v--;
        break;
    case 0x27:
    case 0x28:
        v = *(int *)(s + 0x160) + 1;
        if (v >= *(int *)(s + 0x26c))
            return 1;
        break;
    default:
        return 0;
    }
    *(int *)(s + 0x160) = v;
    *(int *)(s + 0x15c) = v;
    if (!s[0x224])
        notify_594BF0(s);
    return 1;
}
