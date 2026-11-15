/* 0x00429D70: the adjusted-this deleting destructor (this - 0x38) of the object whose base sits 0x38 bytes in:
 * tail-jumps to 0x00429EF0 with the same flag. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00429EF0(void *self, unsigned int flag);

DECOMP(00429D70)
void *__thiscall f_00429D70(void *this, unsigned int flag)
{
    return sub_00429EF0((char *)this - 0x38, flag);
}
