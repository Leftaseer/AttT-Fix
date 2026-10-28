/* 0x004AE660: CTextManager::Render: with texts (+0x68) the vertex stream (SetStreamSource(0, 0x6CA2E0, 0, 20)) and,
 * for each pass of the effect (+0x3C: Begin, BeginPass .. EndPass, End), every text of the list at +0x64 drawn
 * (0x004AE3E0 of its +0x24; the iterator and the end in the statics 0x6CA310 / 0x6CA30C) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AE3E0(void *text);
DECOMP_C char d_006CA314[], d_006CA310[], d_006CA30C[], d_006C8C10[], d_006CA2E0[];
typedef long (__stdcall *SetStreamSource_4AE660)(void *dev, unsigned int n, void *vb, unsigned int off,
                                                   unsigned int stride);
typedef unsigned int (__thiscall *Begin_4AE660)(void *fx, unsigned int *passes, unsigned int flags);
typedef unsigned int (__thiscall *Pass_4AE660)(void *fx, unsigned int i);
typedef unsigned int (__thiscall *End_4AE660)(void *fx);

#define ITER (*(char ***)d_006CA310)
#define END (*(char ***)d_006CA30C)

DECOMP(004AE660)
void __thiscall f_004AE660(void *this)
{
    char *s = (char *)this;
    unsigned int passes = (unsigned int)this, i;
    void **dev, **fx;
    if (!(d_006CA314[0] & 1)) {
        *(unsigned int *)d_006CA314 |= 1;
        ITER = 0;
    }
    if (!(d_006CA314[0] & 2)) {
        *(unsigned int *)d_006CA314 |= 2;
        END = 0;
    }
    if (!*(int *)(s + 0x68))
        return;
    END = *(char ***)(s + 0x64);
    dev = *(void ***)d_006C8C10;
    ((SetStreamSource_4AE660)(*(void ***)dev)[0x190 / 4])(dev, 0, *(void **)d_006CA2E0, 0, 0x14);
    fx = *(void ***)(s + 0x3c);
    ((Begin_4AE660)(*(void ***)fx)[0x18 / 4])(fx, &passes, 0);
    for (i = 0; i < passes; i++) {
        fx = *(void ***)(s + 0x3c);
        ((Pass_4AE660)(*(void ***)fx)[0x20 / 4])(fx, i);
        for (ITER = **(char ****)(s + 0x64); ITER != END; ITER = (char **)*ITER)
            sub_004AE3E0(ITER[9]);
        fx = *(void ***)(s + 0x3c);
        ((End_4AE660)(*(void ***)fx)[0x24 / 4])(fx);
    }
    fx = *(void ***)(s + 0x3c);
    ((End_4AE660)(*(void ***)fx)[0x1c / 4])(fx);
}
