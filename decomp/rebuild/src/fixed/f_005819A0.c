/* 0x005819A0: a constructor: the base (0x00581CB0 with the four floats, a dword and a string), the vtables at +0
 * and +0x214, the empty vector at +0x2A0, then 0x00581760; returns this */
/* @conv ECX 24 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00581CB0(void *self, float a, float b, float c, float d, unsigned int e, void *f);
DECOMP_C void __thiscall sub_00581760(void *self);
DECOMP_C char d_0061DE9C[], d_0061DE90[];

DECOMP(005819A0)
void *__thiscall f_005819A0(void *this, float a, float b, float c, float d, unsigned int e, void *f)
{
    unsigned int *s = (unsigned int *)this;
    sub_00581CB0(this, a, b, c, d, e, f);
    s[0] = (unsigned int)d_0061DE9C;
    s[0x214 / 4] = (unsigned int)d_0061DE90;
    s[0x2a0 / 4] = 0;
    s[0x2a4 / 4] = 0;
    s[0x2a8 / 4] = 0;
    sub_00581760(this);
    return this;
}
