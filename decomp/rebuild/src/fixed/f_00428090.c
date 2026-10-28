/* 0x00428090: for every active entry (+0x1C) of the map at +0x8C, each of its 12-byte items (the vector at +0x20,
 * count 0x00427350) whose random roll (0x004F6630(0, chance * k) / k truncated, chance an unsigned at +4, k the
 * double at 0x68AE10) equals its value (+8) restarts its animation (vf0C(1, 0)) unless it plays (vf20); the map is
 * walked in order (red-black tree, nil flag at +0x31) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_00427350(void *self);
DECOMP_C float __cdecl sub_004F6630(float lo, float hi);
DECOMP_C char d_0068AE10[];
typedef char (__thiscall *vf20_428090)(void *self);
typedef void (__thiscall *vf0C_428090)(void *self, int a, int b);

#define NIL(n) (((char *)(n))[0x31])

DECOMP(00428090)
void __thiscall f_00428090(void *this)
{
    char **head = *(char ***)((char *)this + 0x8c);
    char **n = (char **)*head;
    while (n != head) {
        if (((char *)n)[0x1c]) {
            char *v = (char *)n + 0x20;
            unsigned int i;
            for (i = 0; i < sub_00427350(v); i++) {
                unsigned int *e = (unsigned int *)(*(char **)(v + 4) + i * 0xc);
                double k = *(double *)d_0068AE10;
                float f = (float)((double)e[1] * k);
                int roll = (int)(long long)(sub_004F6630(0.0f, f) / k);
                e = (unsigned int *)(*(char **)(v + 4) + i * 0xc);
                if (roll == (int)e[2]) {
                    void **o = (void **)e[0];
                    if (!((vf20_428090)(*(void ***)o)[0x20 / 4])(o)) {
                        o = *(void ***)(*(char **)(v + 4) + i * 0xc);
                        ((vf0C_428090)(*(void ***)o)[0xc / 4])(o, 1, 0);
                    }
                }
            }
        }
        if (!NIL(n)) {                                  /* ++it */
            char **r = (char **)n[2];
            if (!NIL(r)) {
                while (!NIL(*r))
                    r = (char **)*r;
                n = r;
            } else {
                char **p = (char **)n[1];
                while (!NIL(p) && n == (char **)p[2]) {
                    n = p;
                    p = (char **)p[1];
                }
                n = p;
            }
        }
    }
}
