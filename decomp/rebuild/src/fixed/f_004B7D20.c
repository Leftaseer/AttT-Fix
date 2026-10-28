/* 0x004B7D20: calls 0x4B7BD0 with the argument and a 0x88-byte structure by value, of which only the object at
 * 0x60 is built (0x4CD110 from the argument, given twice by address; the rest is what the original's stack held
 * there: uninitialized here too) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned char b[0x88]; } S88_4B7D20;
DECOMP_C void __thiscall sub_004B7BD0(void *self, unsigned int a, S88_4B7D20 s);
DECOMP_C void __thiscall sub_004CD110(void *obj, unsigned int *a, unsigned int *b);

DECOMP(004B7D20)
void __thiscall f_004B7D20(void *this, unsigned int a)
{
    unsigned int *pa = (unsigned int *)((char *)__builtin_frame_address(0) + 8);   /* the argument's own slot */
    S88_4B7D20 s;
    sub_004CD110(s.b + 0x60, pa, pa);
    sub_004B7BD0(this, *pa, s);
}
