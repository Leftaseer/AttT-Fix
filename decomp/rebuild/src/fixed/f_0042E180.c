/* 0x0042E180: a constructor forwarding to 0x0042DC20 (two vectors by value, copied as dwords, and two floats);
 * returns this (the parameters are dwords: build.py counts parameters, not the dwords of structures) */
/* @conv ECX 32 */
#include "auto_pre.h"
typedef struct { unsigned int x, y, z; } V3_42E180;
DECOMP_C void __thiscall sub_0042DC20(void *self, V3_42E180 a, V3_42E180 b, float c, float d);

DECOMP(0042E180)
void * __thiscall f_0042E180(void *this, unsigned int a0, unsigned int a1, unsigned int a2,
                             unsigned int b0, unsigned int b1, unsigned int b2, float c, float d)
{
    V3_42E180 a = { a0, a1, a2 }, b = { b0, b1, b2 };
    sub_0042DC20(this, a, b, c, d);
    return this;
}
