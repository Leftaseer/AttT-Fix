/* 0x00427D70: applies a new value: clamped to [0, the maximum at 0x0068AE40], pushed into the object at +0x98,
 * kept at +0x94 and in the config's +0x90.  The EAX register argument (the original's key state) is carried along
 * to 0x00427CE0. */
/* @func 00427D70 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00427CE0(void *self, unsigned int eax, float value);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C char d_0068AE40[];

DECOMP(00427D70)
void __cdecl f_00427D70(void *this, unsigned int eax, float value)
{
    if (0.0f > value)
        value = 0.0f;
    else if (value > *(float *)d_0068AE40)
        value = *(float *)d_0068AE40;
    sub_00427CE0((char *)this + 0x98, eax, value);
    *(float *)((char *)this + 0x94) = value;
    *(float *)(sub_00427990() + 0x90) = value;
}
