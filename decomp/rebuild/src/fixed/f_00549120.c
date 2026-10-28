/* CWorldUnit::vf7 0x00549120: hands this to 0x4F5E40 of the object at 0x6C8C3C (the world's unit list) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C undefined4 __thiscall sub_004F5E40(void *list, void *unit);
DECOMP_C char d_006C8C3C[];

DECOMP(00549120)
int __thiscall f_00549120(void *this)
{
    sub_004F5E40(*(void **)d_006C8C3C, this);
    return 0;
}
