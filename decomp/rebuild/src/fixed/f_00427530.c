/* 0x00427530: sets the time t of the animation (+8: vf18(t, 0); at the end time 0x60FAC0 vf10, else unless it plays
 * (vf20) vf0C(0, 0)) and of each attached one (12-byte elements of the vector at +0x14); returns the count of those
 * (0 without the vector) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_0060FAC0[];
typedef void (__thiscall *vf18_427530)(void *self, float t, int flag);
typedef unsigned int (__thiscall *vf_427530)(void *self);
typedef void (__thiscall *vf0C_427530)(void *self, int a, int b);

DECOMP(00427530)
unsigned int __thiscall f_00427530(void *this, float t)
{
    char *s = (char *)this;
    void **a = *(void ***)(s + 8);
    unsigned int i, n;
    ((vf18_427530)(*(void ***)a)[0x18 / 4])(a, t, 0);
    a = *(void ***)(s + 8);
    if (t == *(float *)d_0060FAC0)
        ((vf_427530)(*(void ***)a)[0x10 / 4])(a);
    else if (!(char)((vf_427530)(*(void ***)a)[0x20 / 4])(a)) {
        a = *(void ***)(s + 8);
        ((vf0C_427530)(*(void ***)a)[0xc / 4])(a, 0, 0);
    }
    for (i = 0;; i++) {
        char *v = *(char **)(s + 0x14);
        void **o;
        if (!v)
            return 0;
        n = (unsigned int)((int)(*(char **)(s + 0x18) - v) / 0xc);
        if (i >= n)
            return n;
        o = *(void ***)(v + i * 0xc);
        ((vf18_427530)(*(void ***)o)[0x18 / 4])(o, t, 0);
    }
}
