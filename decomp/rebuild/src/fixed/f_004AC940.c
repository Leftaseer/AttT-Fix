/* 0x004AC940: moves to (x, z): keeps the old position (+0x64..+0x6C) at +0x58, sets x and z and the height y from
 * the terrain (0x00473110), marks the position changed (+0x1AD, +0x70) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C char d_006CA2D0[];

DECOMP(004AC940)
void __thiscall f_004AC940(void *this, float x, float z)
{
    char *s = (char *)this;
    *(unsigned int *)(s + 0x58) = *(unsigned int *)(s + 0x64);
    *(unsigned int *)(s + 0x5c) = *(unsigned int *)(s + 0x68);
    *(unsigned int *)(s + 0x60) = *(unsigned int *)(s + 0x6c);
    *(float *)(s + 0x64) = x;
    s[0x1ad] = 1;
    *(float *)(s + 0x68) = sub_00473110(*(void **)d_006CA2D0, x, z);
    *(float *)(s + 0x6c) = z;
    s[0x70] = 1;
}
