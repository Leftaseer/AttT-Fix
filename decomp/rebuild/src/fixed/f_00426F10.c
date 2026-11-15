/* 0x00426F10: hands the +8 callback the address of the third argument between the second and third ones, and stores
 * the pointed-to dword of its result through the first argument. */
/* @conv ECX 12 */
#include "auto_pre.h"

DECOMP(00426F10)
void __thiscall f_00426F10(void *this, unsigned int *out, unsigned int a, unsigned int b)
{
    unsigned int *r = (unsigned int *)(*(unsigned int *(__thiscall **)(void *, unsigned int *, unsigned int,
                                                                     unsigned int))((char *)this + 8))(this, &b, a, b);
    *out = *r;
}
