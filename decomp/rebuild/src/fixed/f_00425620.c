/* 0x00425620: C3DLine::vf37 (its two arguments unused): vf2D(0), then for each pass of the line effect (0x6C870C) the
 * line drawn: texture factor (+0x1C8) and z test (+0x1CC) render states, its vertex buffer (+0x1C4, 12-byte
 * vertices) and DrawPrimitive(D3DPT_LINELIST, 0, 1); then vf2E, whose result is returned */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_006C870C[], d_006C8C10[];
typedef unsigned int (__thiscall *vf_425620)(void *self);
typedef void (__thiscall *vf1_425620)(void *self, unsigned int a);
typedef unsigned int (__thiscall *Begin_425620)(void *fx, unsigned int *passes, unsigned int flags);
typedef long (__stdcall *SetRS_425620)(void *dev, unsigned int state, unsigned int v);
typedef long (__stdcall *SetSS_425620)(void *dev, unsigned int n, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *Draw_425620)(void *dev, unsigned int type, unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define FX (*(void ***)d_006C870C)

DECOMP(00425620)
unsigned int __thiscall f_00425620(void *this, unsigned int a, unsigned int b)
{
    char *s = (char *)this;
    unsigned int passes = (unsigned int)this, i;
    ((vf1_425620)(*(void ***)this)[0xb4 / 4])(this, 0);
    ((Begin_425620)(*(void ***)FX)[0x18 / 4])(FX, &passes, 0);
    for (i = 0; i < passes; i++) {
        ((vf1_425620)(*(void ***)FX)[0x20 / 4])(FX, i);
        ((SetRS_425620)(*(void ***)DEV)[0xe4 / 4])(DEV, 0x3c, *(unsigned int *)(s + 0x1c8));     /* D3DRS_TEXTUREFACTOR */
        ((SetRS_425620)(*(void ***)DEV)[0xe4 / 4])(DEV, 7, s[0x1cc] != 0);                      /* D3DRS_ZENABLE */
        ((SetSS_425620)(*(void ***)DEV)[0x190 / 4])(DEV, 0, *(void **)(s + 0x1c4), 0, 0xc);
        ((Draw_425620)(*(void ***)DEV)[0x144 / 4])(DEV, 2, 0, 1);
        ((vf_425620)(*(void ***)FX)[0x24 / 4])(FX);
    }
    ((vf_425620)(*(void ***)FX)[0x1c / 4])(FX);
    return ((vf_425620)(*(void ***)this)[0xb8 / 4])(this);
}
