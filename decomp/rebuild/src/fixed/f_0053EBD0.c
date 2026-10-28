/* 0x0053EBD0: builds a menu screen's buttons: a new 0x74-byte container (0x00426DF0) at +0xC8, added as a child
 * (0x004205C0); for each layout entry of +0x7C's +0x114 vector (0x2C bytes) but the last two, a new 0x28C-byte button
 * (0x004699B0 on this and the entry) placed (its +0x54 part: vf68 at the entry's +0x1C/+0x20, vf94 sized +0x24/+0x28)
 * with its click handler by position (the first five: 0x0053D600, 0x0053DA80, 0x0053DF40, 0x0053E140, 0x0053DD40)
 * and two more (0x0053A9D0, 0x0053A980), each wrapped by 0x0053AA30, put in the container (0x00426EC0), registered
 * with this (+0x04 vf04) and with the tooltips 0x006CAAAC (0x0046A200) (the original frees the button if its
 * construction throws; this C does not) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00426DF0(void *self);
DECOMP_C void __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char *__thiscall sub_004699B0(void *self, void *owner, void *entry);
DECOMP_C void *__cdecl sub_0053AA30(void *fn, int a);
DECOMP_C void __thiscall sub_00426EC0(void *self, void *item);
DECOMP_C void __thiscall sub_0046A200(void *self, void *entry, void *item);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_0053D600[], d_0053DA80[], d_0053DF40[], d_0053E140[], d_0053DD40[], d_0053A9D0[], d_0053A980[],
    d_006CAAAC[];
typedef void (__thiscall *xy_53EBD0)(void *self, float x, float y);
typedef void (__thiscall *add_53EBD0)(void *self, void *item);

DECOMP(0053EBD0)
void __thiscall f_0053EBD0(void *this)
{
    static char *const fns[5] = { d_0053D600, d_0053DA80, d_0053DF40, d_0053E140, d_0053DD40 };
    char *s = (char *)this;
    char *vec, *b, *e;
    void *m, **ui;
    unsigned int n, i;
    m = sub_005E3EAE(0x74);
    m = m ? sub_00426DF0(m) : 0;
    *(void **)(s + 0xc8) = m;
    sub_004205C0(this, m);
    vec = *(char **)(s + 0x7c) + 0x114;
    n = (*(char **)(vec + 4) ? (int)(*(char **)(vec + 8) - *(char **)(vec + 4)) / 0x2c : 0) - 2;
    for (i = 0; i < n; i++) {
        m = sub_005E3EAE(0x28c);
        b = m ? sub_004699B0(m, this, *(char **)(vec + 4) + i * 0x2c) : 0;
        ui = (void **)(b + 0x54);
        e = *(char **)(vec + 4) + i * 0x2c;
        ((xy_53EBD0)(*(void ***)ui)[0x68 / 4])(ui, *(float *)(e + 0x1c), *(float *)(e + 0x20));
        e = *(char **)(vec + 4) + i * 0x2c;
        ((xy_53EBD0)(*(void ***)ui)[0x94 / 4])(ui, *(float *)(e + 0x24), *(float *)(e + 0x28));
        if (i <= 4)
            *(void **)(b + 0xc) = sub_0053AA30(fns[i], 0);
        *(void **)(b + 0x10) = sub_0053AA30(d_0053A9D0, 0);
        *(void **)(b + 0x14) = sub_0053AA30(d_0053A980, 0);
        sub_00426EC0(*(void **)(s + 0xc8), b);
        ((add_53EBD0)(*(void ***)(s + 4))[1])(s + 4, ui);
        sub_0046A200(*(void **)d_006CAAAC, *(char **)(vec + 4) + i * 0x2c, b);
    }
}
