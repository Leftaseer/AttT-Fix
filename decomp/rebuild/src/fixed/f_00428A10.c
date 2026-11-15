/* 0x00428A10: registers the ambient sound manager (the object passed in) as the global "AmbientSoundManager". */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004287C0(const char *name, unsigned int value);
DECOMP_C char d_006082D4[];

DECOMP(00428A10)
void __thiscall f_00428A10(unsigned int value)
{
    sub_004287C0(d_006082D4, value);
}
