/* 0x00463300: the fractional part of param_1 is added to +0x4ac (mode 0) or +0x4b0 (modes 1, 2); the original
 * does fild/fadd dword/fmul qword/fadd qword/fistp qword in extended precision, while the decompiler's
 * '(float)' cast made clang round the product to a float (fstp dword/fld dword) before the fistp */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[];
DECOMP_C char d_0060BF38[];
DECOMP_C char d_0068AE08[];

DECOMP(00463300)
undefined4 __thiscall f_00463300(void *this, int param_1)
{
    int mode = *(int *)((int)this + 0x4a8);
    double v = (double)param_1;
    int lo;

    if (param_1 < 0) v += (double)*(float *)d_0068AE08;
    if (mode == 0 || mode == 1) {
        v = v * *(double *)d_0060BF38 + *(double *)d_00607CE0;
        lo = (int)(longlong)v;
        if (mode == 0) {
            *(int *)((int)this + 0x4ac) += lo;
            *(int *)((int)this + 0x4b0) += param_1 - lo;
        } else {
            *(int *)((int)this + 0x4b0) += lo;
            *(int *)((int)this + 0x4ac) += param_1 - lo;
        }
        return CONCAT31((uint)lo >> 8, 1);
    }
    if (mode == 2) {
        v = v * *(double *)d_00607CE0 + *(double *)d_00607CE0;
        lo = (int)(longlong)v;
        *(int *)((int)this + 0x4b0) += lo;
        *(int *)((int)this + 0x4ac) += param_1 - lo;
        return CONCAT31((uint)lo >> 8, 1);
    }
    return CONCAT31((uint)(mode - 2) >> 8, 1);
}
