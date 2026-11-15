/* 0x004CC6D0: StandardList vf slot: sets the animation time on the object 0x10 bytes before this and on this
 * itself (0x4F6180); returns the latter's result. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_004CC460(void *self, float t);
DECOMP_C int __thiscall sub_004F6180(void *self, float t);

DECOMP(004CC6D0)
int __thiscall f_004CC6D0(char *this, float t)
{
    sub_004CC460(this - 0x10, t);
    return sub_004F6180(this, t);
}
