/* 0x004F7390: resets the object at +4 and passes the four integer arguments on, converted to floats, to the
 * setter at +0x1C. */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00430CD0(void *self);
DECOMP_C int __thiscall sub_004CA820(void *self, float a, float b, float c, float d);

DECOMP(004F7390)
int __thiscall f_004F7390(char *this, int a, int b, int c, int d)
{
    sub_00430CD0(this + 4);
    return sub_004CA820(this + 0x1c, (float)a, (float)b, (float)c, (float)d);
}
