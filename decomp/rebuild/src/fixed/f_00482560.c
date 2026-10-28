/* 0x00482560: shows the current page (+0x224) of a paged dialog: marks it shown (+0x298), the frame (+0x290: vf4C,
 * then vf34 with its texture: the page's own pair for the first three pages (+0x240, 8 bytes each), else by parity
 * (+0x258 / +0x260), the second of the pair unless it is the last page (pages: 28-byte entries +0x22C..+0x230)), the
 * picture (+0x29C, 0x00473D20, which takes it in EAX too) by the page and the entry's +0x40 of +0x23C; the page count
 * at the last page lowers the counter +0x238; returns the count less that counter */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00473D20(void *self, unsigned int eax, unsigned int tex);
typedef void (__thiscall *vf_482560)(void *self);
typedef void (__thiscall *vf1_482560)(void *self, unsigned int a);

#define PAGES(s) (*(char **)((s) + 0x22c) ? (int)(*(char **)((s) + 0x230) - *(char **)((s) + 0x22c)) / 0x1c : 0)
#define U(o) (*(unsigned int *)(s + (o)))

DECOMP(00482560)
int __thiscall f_00482560(void *this)
{
    char *s = (char *)this;
    void **fr = *(void ***)(s + 0x290);
    int i, n, r, k;
    unsigned int a, b, t;
    s[0x298] = 1;
    ((vf_482560)(*(void ***)fr)[0x4c / 4])(fr);
    i = *(int *)(s + 0x224);
    if (i < 3) {
        a = U(0x240 + i * 8);
        b = U(0x244 + i * 8);
    } else {
        int idx = i % 2 ? -1 : 0;
        a = U(0x260 + idx * 8);
        b = U(0x264 + idx * 8);
    }
    if (*(char **)(s + 0x22c) && PAGES(s) && (unsigned int)i != (unsigned int)(PAGES(s) - 1))
        a = b;
    fr = *(void ***)(s + 0x290);
    ((vf1_482560)(*(void ***)fr)[0x34 / 4])(fr, a);
    i = *(int *)(s + 0x224);
    k = *(int *)(*(char **)(s + 0x23c) + 0x40);
    switch (i) {
    case 0: t = k == 0 ? U(0x268) : U(0x26c); break;
    case 1: t = k == 0x2e ? U(0x270) : U(0x274); break;
    case 2: t = k == 0x5c ? U(0x278) : U(0x27c); break;
    default:
        if (i % 2 == 0)
            t = k == 0xb8 ? U(0x288) : U(0x28c);
        else
            t = k == 0x8a ? U(0x280) : U(0x284);
    }
    sub_00473D20(*(void **)(s + 0x29c), t, t);
    n = PAGES(s);
    r = n - *(unsigned short *)(s + 0x238);
    if (*(int *)(s + 0x224) == r)
        *(unsigned short *)(s + 0x238) = *(unsigned short *)(s + 0x238) - 1;
    return r;
}
