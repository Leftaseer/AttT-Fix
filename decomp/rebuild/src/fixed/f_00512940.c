/* 0x00512940: hands the node's texture [0x3C4] to the animation object at [0x3D0] and stores the frame
 * count it returns at [0x3CC]. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042DEE0(void *self, void *texture);
DECOMP_C int __thiscall sub_0042D9A0(void *self);

DECOMP(00512940)
int __thiscall f_00512940(char *this)
{
    void *animation = *(void **)(this + 0x3d0);
    sub_0042DEE0(animation, *(void **)(this + 0x3c4));
    return *(int *)(this + 0x3cc) = sub_0042D9A0(*(void **)(this + 0x3d0));
}
