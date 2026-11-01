/* 0x00458290: for each plane index in the table at 0x6C0730 checks whether one of the four points
 * (param_1 + 0/0xc/0x18/0x24) is in front of the plane at this + idx*0x10 (dot > 0); if a plane has no
 * point in front it returns 0, otherwise 1 after all planes. The original compares with fcomi + ja (and
 * jbe for the last corner), so an unordered dot counts as "not in front" instead of falling through the
 * C <= chain. The index being tested is published at 0x6C8DDC. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C char d_006C0730[], d_006C8DDC[];

DECOMP(00458290)
undefined4 __thiscall f_00458290(void *this, float *param_1)
{
    int *pi;
    uint off = 0;

    for (pi = (int *)d_006C0730; (int)pi <= 0x6C073C; pi++) {
        int idx = *pi;
        float *pl;
        int k;
        int in_front = 0;

        off = (uint)idx * 0x10;
        *(int *)d_006C8DDC = idx;
        pl = (float *)((int)this + off);
        for (k = 0; k < 4; k++) {
            float *p = param_1 + 3 * k;
            float dot = ((pl[1] * p[0] + pl[2] * p[1]) + pl[3] * p[2]) + pl[4];
            if (dot > 0.0f) {
                in_front = 1;
                break;
            }
        }
        if (!in_front)
            return (off >> 8) << 8;
    }
    return ((off >> 8) & 0xFFFFFF00u) | 1;
}
