/* 0x0048A2C0: fills the 0x30 bytes of param_3 with two rows of a quad: y = i*F(0x5c) + F(0x70) and
 * z = F(0x78) - j*F(0x60), i and j as floats (biased by 2^32 when negative, the unsigned conversion), each
 * rounded to float once (fstp dword [esp+0x14], [esp+0xc]) and reused from the rounded value.  The generated
 * code computed the whole expression in extended precision. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_0068AE08[];
DECOMP_C void *__cdecl sub_005E40BE(void *dst, int val, unsigned int size);

DECOMP(0048A2C0)
void __thiscall f_0048A2C0(void *this, int param_1, int param_2, float *param_3)
{
    double i = (double)param_1, j = (double)param_2;
    volatile float y, z;

    sub_005E40BE(param_3, 0, 0x30);
    if (param_1 < 0)
        i = i + (double)*(float *)d_0068AE08;
    y = (float)(i * *(float *)((char *)this + 0x5c) + *(float *)((char *)this + 0x70));
    if (param_2 < 0)
        j = j + (double)*(float *)d_0068AE08;
    z = (float)(*(float *)((char *)this + 0x78) - j * *(float *)((char *)this + 0x60));
    param_3[0] = y;
    param_3[2] = z;
    param_3[3] = y + *(float *)((char *)this + 0x5c);
    param_3[5] = z;
    param_3[6] = *(float *)((char *)this + 0x5c) + y;
    param_3[9] = y;
    param_3[8] = z - *(float *)((char *)this + 0x60);
    param_3[0xb] = z - *(float *)((char *)this + 0x60);
}
