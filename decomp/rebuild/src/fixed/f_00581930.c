/* 0x00581930: a constructor: the base (0x00581E00, which takes EBX as it came), the vtables at +0 and +0x214, the
 * empty vector at +0x2A0, then 0x00581760; returns this */
/* @conv ECX,EBX 4 */
#include "auto_pre.h"
/* @func 00581930 custom */
DECOMP_C void *__cdecl sub_00581E00(void *self, unsigned int ebx, void *a);
DECOMP_C void __thiscall sub_00581760(void *self);
DECOMP_C char d_0061DE9C[], d_0061DE90[];

DECOMP(00581930)
void *__cdecl f_00581930(void *this, unsigned int ebx, void *a)
{
    unsigned int *s = (unsigned int *)this;
    sub_00581E00(this, ebx, a);
    s[0] = (unsigned int)d_0061DE9C;
    s[0x214 / 4] = (unsigned int)d_0061DE90;
    s[0x2a0 / 4] = 0;
    s[0x2a4 / 4] = 0;
    s[0x2a8 / 4] = 0;
    sub_00581760(this);
    return this;
}
