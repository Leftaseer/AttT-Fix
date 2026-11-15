/* 0x00426FB0: stores the float at +0x2C and tells the +0x18 virtual about it, passing on the double from the
 * +0x1C virtual (truncated to float) and 1.  The +0x18 slot is read after the first call. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00426FB0)
void __thiscall f_00426FB0(void *this, float value)
{
    char *s = (char *)this;
    void (__thiscall *fn)(void *, float, unsigned int);
    double d = (*(double (__thiscall **)(void *))(*(char **)s + 0x1c))(s);
    fn = *(void (__thiscall **)(void *, float, unsigned int))(*(char **)s + 0x18);
    *(float *)(s + 0x2c) = value;
    fn(s, (float)d, 1);
}
