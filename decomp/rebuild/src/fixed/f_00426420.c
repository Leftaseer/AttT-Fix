/* 0x00426420: scales a 2D vector by 1 / param_2; the factor is rounded to float as the original stores it */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00426420)
void __thiscall f_00426420(void *this, float *param_1, float param_2)
{
    volatile float k = 1.0f / param_2;

    *param_1 = k * *(float *)this;
    param_1[1] = k * *(float *)((int)this + 4);
}
