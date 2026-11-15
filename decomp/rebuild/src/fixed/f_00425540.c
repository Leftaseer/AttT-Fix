/* 0x00425540: C3DLine's batch draw: updates the world transform (0x004AC890), then for each pass of the line effect
 * (0x006C870C) draws the line — texture factor (+0x1C8) and z test (+0x1CC) render states, its vertex buffer
 * (+0x1C4, 12-byte vertices) as a one-segment line list — and returns the effect's slot 0x1C value.  The pass count
 * is handed to the begin slot initialized with this, which replaces it. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_006C870C[], d_006C8C10[];
DECOMP_C void __thiscall sub_004AC890(void *self);
typedef unsigned int (__thiscall *vf_425540)(void *self);
typedef void (__thiscall *vf1_425540)(void *self, unsigned int a);
typedef unsigned int (__thiscall *Begin_425540)(void *fx, unsigned int *passes, unsigned int flags);
typedef long (__stdcall *SetRS_425540)(void *dev, unsigned int state, unsigned int v);
typedef long (__stdcall *SetSS_425540)(void *dev, unsigned int n, void *vb, unsigned int off, unsigned int stride);
typedef long (__stdcall *Draw_425540)(void *dev, unsigned int type, unsigned int start, unsigned int count);

#define DEV (*(void ***)d_006C8C10)
#define FX (*(void ***)d_006C870C)

DECOMP(00425540)
unsigned int __thiscall f_00425540(void *this)
{
    char *s = (char *)this;
    unsigned int passes = (unsigned int)this, i;
    sub_004AC890(this);
    ((Begin_425540)(*(void ***)FX)[0x18 / 4])(FX, &passes, 0);
    for (i = 0; i < passes; i++) {
        ((vf1_425540)(*(void ***)FX)[0x20 / 4])(FX, i);
        ((SetRS_425540)(*(void ***)DEV)[0xe4 / 4])(DEV, 0x3c, *(unsigned int *)(s + 0x1c8));     /* D3DRS_TEXTUREFACTOR */
        ((SetRS_425540)(*(void ***)DEV)[0xe4 / 4])(DEV, 7, s[0x1cc] != 0);                      /* D3DRS_ZENABLE */
        ((SetSS_425540)(*(void ***)DEV)[0x190 / 4])(DEV, 0, *(void **)(s + 0x1c4), 0, 0xc);
        ((Draw_425540)(*(void ***)DEV)[0x144 / 4])(DEV, 2, 0, 1);
        ((vf_425540)(*(void ***)FX)[0x24 / 4])(FX);
    }
    return ((vf_425540)(*(void ***)FX)[0x1c / 4])(FX);
}
