/* 0x00425710: the same batch draw without the world transform update (0x00425540 does that): for each pass of the line
 * effect (0x006C870C) it comes the line — texture factor (+0x1C8) and z test (+0x1CC) render states, its vertex
 * buffer (+0x1C4, 12-byte vertices) as a one-segment line list — and the effect's slot 0x1C value is dropped.  The
 * pass count is handed to the begin slot initialized with this, which replaces it. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006C870C[], d_006C8C10[];
typedef unsigned int (__thiscall *vf_425710)(void *self);
typedef void (__thiscall *vf1_425710)(void *self, unsigned int a);
typedef unsigned int (__thiscall *Begin_425710)(void *fx, unsigned int *passes, unsigned int flags);
typedef long (__stdcall *SetRS_425710)(void *dev, unsigned int state, unsigned int v);
typedef long (__stdcall *SetSS_425710)(void *dev, unsigned int n, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *Draw_425710)(void *dev, unsigned int type, unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define FX (*(void ***)d_006C870C)

DECOMP(00425710)
void __thiscall f_00425710(void *this)
{
    char *s = (char *)this;
    unsigned int passes = (unsigned int)this, i;
    ((Begin_425710)(*(void ***)FX)[0x18 / 4])(FX, &passes, 0);
    for (i = 0; i < passes; i++) {
        ((vf1_425710)(*(void ***)FX)[0x20 / 4])(FX, i);
        ((SetRS_425710)(*(void ***)DEV)[0xe4 / 4])(DEV, 0x3c, *(unsigned int *)(s + 0x1c8));     /* D3DRS_TEXTUREFACTOR */
        ((SetRS_425710)(*(void ***)DEV)[0xe4 / 4])(DEV, 7, s[0x1cc] != 0);                      /* D3DRS_ZENABLE */
        ((SetSS_425710)(*(void ***)DEV)[0x190 / 4])(DEV, 0, *(void **)(s + 0x1c4), 0, 0xc);
        ((Draw_425710)(*(void ***)DEV)[0x144 / 4])(DEV, 2, 0, 1);
        ((vf_425710)(*(void ***)FX)[0x24 / 4])(FX);
    }
    ((vf_425710)(*(void ***)FX)[0x1c / 4])(FX);
}
