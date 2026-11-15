/* 0x004263F0: the mirror of the 2D position (+0/+4) about the screen edge 0x00608088 into the vector;
 * returns the vector */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608088[];

DECOMP(004263F0)
void *__thiscall f_004263F0(void *this, float *out)
{
    char *s = (char *)this;
    float edge = *(float *)d_00608088;
    out[0] = edge - *(float *)(s + 0);
    out[1] = edge - *(float *)(s + 4);
    return out;
}
