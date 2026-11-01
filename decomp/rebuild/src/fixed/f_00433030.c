/* 0x00433030: scales a 3D vector by 1 / param_2; the factor is rounded to float as the original stores it */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00433030)
void __thiscall f_00433030(void *this, float *param_1, float param_2)
{
    volatile float k = 1.0f / param_2;

    *param_1 = k * *(float *)this;
    param_1[1] = k * *(float *)((int)this + 4);
    param_1[2] = k * *(float *)((int)this + 8);
}
