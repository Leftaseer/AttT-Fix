/* 0x0044B920: feeds the mouse to the GUI (+0x5C: vf2C, a window procedure) when it has one: the cursor (+0x90:
 * vf04(0), position vf88) as the LPARAM, the button and key flags (MK_SHIFT / MK_CONTROL from the key states +0x13B /
 * +0x13C, MK_MBUTTON / MK_RBUTTON / MK_LBUTTON from +0x7C6 / +0x7C4 / +0x7C5 of 0x004215D0's input) as the WPARAM; a
 * move (+0x650 / +0x654 nonzero) as WM_MOUSEMOVE, then each queued button event (+0x66C, count +0x670) as its
 * message, marked 6 when taken */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C char d_006C889C[];
typedef void (__thiscall *vf04_44B920)(void *self, float v);
typedef float *(__thiscall *vf88_44B920)(void *self);
typedef char (__thiscall *proc_44B920)(void *self, void *hwnd, unsigned int msg, unsigned int wp, unsigned int lp);

DECOMP(0044B920)
void __thiscall f_0044B920(void *this)
{
    static const unsigned int msgs[6] = { 0x201, 0x202, 0x204, 0x205, 0x207, 0x208 };
    char *s = (char *)this;
    char *in;
    unsigned int *ev, n, i, wp, lp;
    void **c, **g;
    float *p;
    if (!*(void **)(s + 0x5c))
        return;
    in = sub_004215D0();
    ev = *(unsigned int **)(in + 0x66c);
    n = *(unsigned int *)(in + 0x670);
    c = *(void ***)(s + 0x90);
    ((vf04_44B920)(*(void ***)c)[1])(c, 0.0f);
    c = *(void ***)(s + 0x90);
    p = ((vf88_44B920)(*(void ***)c)[0x88 / 4])(c);
    lp = (unsigned int)(unsigned short)(int)p[1] << 16 | (unsigned short)(int)p[0];
    wp = (((unsigned char)in[0x13b] >> 1 & 0x40) | ((unsigned char)in[0x13c] & 0x80)) >> 4 |
         (in[0x7c6] ? 0x10 : 0) | (in[0x7c4] ? 2 : 0) | (in[0x7c5] != 0);
    if (*(float *)(in + 0x650) != 0.0f || *(float *)(in + 0x654) != 0.0f) {
        g = *(void ***)(s + 0x5c);
        ((proc_44B920)(*(void ***)g)[0x2c / 4])(g, *(void **)d_006C889C, 0x200, wp, lp);
    }
    for (i = 0; i < n; i++)
        if (ev[i] <= 5) {
            g = *(void ***)(s + 0x5c);
            if (((proc_44B920)(*(void ***)g)[0x2c / 4])(g, *(void **)d_006C889C, msgs[ev[i]], wp, lp))
                ev[i] = 6;
        }
}
