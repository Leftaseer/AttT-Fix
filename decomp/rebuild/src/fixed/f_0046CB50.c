/* 0x0046CB50: the mouse's per-frame poll: while acquired (+0x7C8) it reads up to 0x40 buffered DirectInput events
 * (device +0x148, GetDeviceData into +0x150, count +0x14C, result +0x40); on failure it re-acquires (looping while
 * DIERR_OTHERAPPHASPRIO 0x8007001E) and clears the frame's motion (+0x650..+0x658) and button log (+0x670); otherwise
 * it sums the X / Y / wheel offsets (+0x650 / +0x654 / +0x658, marking motion at +0x7C9) and turns button 0 / 1 / 2
 * presses and releases into the log (+0x66C array, codes 0..5), their held flags (+0x7C5 / +0x7C4 / +0x7C6) and the
 * button event lists 0x006C9014..0x006C903C (0x0044A3F0 with an empty event 0x0060AC14; a press of the left or right
 * button counts only while the world is shown (0x006C88D8 +0x40) or the other is up); with motion each listener of
 * 0x006C9054 (next kept at 0x006C9058) gets a move event (0x0060C798, x, y, wheel) through vf04. Returns what the
 * original leaves in EAX (EAX unchanged when not acquired) */
/* @conv ECX,EAX 0 */
/* @func 0046CB50 custom */
#include "auto_pre.h"
DECOMP_C unsigned int __cdecl sub_0044A3F0(void *self, unsigned int eax, void *ev);
DECOMP_C char d_006C88D8[], d_0060AC14[], d_0060C798[], d_006C9014[], d_006C901C[], d_006C9024[], d_006C902C[],
    d_006C9034[], d_006C903C[], d_006C9054[], d_006C9058[];
typedef int (__stdcall *getdata_46CB50)(void *dev, unsigned int size, void *data, unsigned int *n, unsigned int fl);
typedef int (__stdcall *acquire_46CB50)(void *dev);
typedef unsigned int (__thiscall *move_46CB50)(void *self, void *ev);

#define F(o) (*(float *)(s + (o)))

static unsigned int log_46CB50(char *s, int code, char *list, int base)
{
    unsigned int i = *(unsigned int *)(s + 0x670), *a = *(unsigned int **)(s + 0x66c);
    void *ev = d_0060AC14;
    a[i] = code;
    *(unsigned int *)(s + 0x670) = i + 1;
    return sub_0044A3F0(list, base ? (unsigned int)a : i, &ev);
}

DECOMP(0046CB50)
unsigned int __cdecl f_0046CB50(void *this, unsigned int eax)
{
    char *s = (char *)this, *dev;
    unsigned int k;
    int hr;
    if (!s[0x7c8])
        return eax;
    dev = *(char **)(s + 0x148);
    *(unsigned int *)(s + 0x14c) = 0x40;
    hr = ((getdata_46CB50)(*(void ***)dev)[0x28 / 4])(dev, 0x14, s + 0x150, (unsigned int *)(s + 0x14c), 0);
    *(int *)(s + 0x40) = hr;
    if (hr) {
        dev = *(char **)(s + 0x148);
        hr = ((acquire_46CB50)(*(void ***)dev)[0x1c / 4])(dev);
        *(int *)(s + 0x40) = hr;
        while (hr == -0x7ff8ffe2) {
            dev = *(char **)(s + 0x148);
            hr = ((acquire_46CB50)(*(void ***)dev)[0x1c / 4])(dev);
            *(int *)(s + 0x40) = hr;
        }
        *(unsigned int *)(s + 0x670) = 0;
        F(0x658) = 0;
        F(0x654) = 0;
        F(0x650) = 0;
        return (unsigned int)hr;
    }
    F(0x658) = 0;
    F(0x654) = 0;
    F(0x650) = 0;
    *(unsigned int *)(s + 0x670) = 0;
    s[0x7c9] = 0;
    eax = 0;
    for (k = 0; k < *(unsigned int *)(s + 0x14c); k++) {
        unsigned int *e = (unsigned int *)(s + 0x150 + k * 0x14);
        int down = ((unsigned char *)e)[4] & 0x80;
        switch (e[0]) {
        case 0:
            F(0x650) = (float)(int)e[1] + F(0x650);
            s[0x7c9] = 1;
            break;
        case 4:
            F(0x654) = (float)(int)e[1] + F(0x654);
            s[0x7c9] = 1;
            break;
        case 8:
            F(0x658) = (float)(int)e[1] + F(0x658);
            s[0x7c9] = 1;
            break;
        case 0xc:
            if (down) {
                if (!(*(char **)d_006C88D8)[0x40] && s[0x7c4])
                    break;
                s[0x7c5] = 1;
                log_46CB50(s, 0, d_006C9014, 1);
            } else {
                s[0x7c5] = 0;
                log_46CB50(s, 1, d_006C901C, 1);
            }
            break;
        case 0xd:
            if (down) {
                if (!(*(char **)d_006C88D8)[0x40] && s[0x7c5])
                    break;
                s[0x7c4] = 1;
                log_46CB50(s, 2, d_006C9024, 0);
            } else {
                s[0x7c4] = 0;
                log_46CB50(s, 3, d_006C902C, 0);
            }
            break;
        case 0xe:
            if (down) {
                s[0x7c6] = 1;
                log_46CB50(s, 4, d_006C9034, 0);
            } else {
                s[0x7c6] = 0;
                log_46CB50(s, 5, d_006C903C, 0);
            }
            break;
        }
        eax = k + 1;
    }
    if (s[0x7c9]) {
        struct { void *vt; float x, y, z; } ev;
        char *l;
        ev.vt = d_0060C798;
        ev.x = F(0x650);
        ev.y = F(0x654);
        ev.z = F(0x658);
        eax = *(unsigned int *)(s + 0x650);
        for (l = *(char **)d_006C9054; l; l = *(char **)d_006C9058) {
            *(void **)d_006C9058 = *(void **)(l + 4);
            eax = ((move_46CB50)(*(void ***)l)[1])(l, &ev);
        }
    }
    return eax;
}
