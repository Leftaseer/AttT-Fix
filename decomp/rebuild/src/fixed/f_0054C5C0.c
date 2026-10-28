/* 0x0054C5C0: a delegate callback (fn(ctx in ECX, a, b), pop 8): *a = |*b| (as a float); then by the state the
 * delegate at +0x59C reports (its function +0xC, context +0x14, given its +8): 1-4 chain to its delegate at +0x18
 * (function +0x20, context +0x24) with that and a; 5 and above call the delegate at +0x5A4 (context +0x5A8) with
 * +0x59C and a pointer to 0; 0 nothing */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef int (__thiscall *dlg1_54C5C0)(void *ctx, void *a);
typedef void (__thiscall *dlg2_54C5C0)(void *ctx, void *a, void *b);

DECOMP(0054C5C0)
void __thiscall f_0054C5C0(void *this, float *a, float *b)
{
    char *s = (char *)this;
    char *d = *(char **)(s + 0x59c);
    unsigned int zero = 0;
    float v = *b;
    *a = __builtin_fabsf(v);
    switch (((dlg1_54C5C0)*(void **)(d + 0xc))(*(void **)(d + 0x14), d + 8)) {
    case 0:
        return;
    case 1: case 2: case 3: case 4:
        d = *(char **)(s + 0x59c);
        ((dlg2_54C5C0)*(void **)(d + 0x20))(*(void **)(d + 0x24), d + 0x18, a);
        return;
    default:
        ((dlg2_54C5C0)*(void **)(s + 0x5a4))(*(void **)(s + 0x5a8), s + 0x59c, &zero);
    }
}
