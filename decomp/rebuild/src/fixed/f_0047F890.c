/* 0x0047F890: in-place 45-degree rotation of a 2x2 pair in a 4-float record; the original rounds the two
 * sums (z+x, w+y) to float in a stack slot before halving them, which the generated form kept extended */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0047F890)
void __fastcall f_0047F890(float *param_1)
{
    volatile float s1, s2, c, d, a, b, e, f;
    float x0 = param_1[0];
    float y0 = param_1[1];
    float z0 = param_1[2];
    float w0 = param_1[3];

    s1 = z0 + x0;
    s2 = w0 + y0;
    c = w0 - y0;
    d = z0 - x0;
    a = s1 * 0.5f;
    b = s2 * 0.5f;
    e = c * 0.5f;
    f = d * -0.5f;

    param_1[0] = a - e;
    param_1[1] = b - f;
    param_1[2] = a + e;
    param_1[3] = b + f;
}
