/* 0x0042D940: the record `index` of the frame array (+0 holds the records, +0xC their stride count): a record is
 * 0x18 bytes; an out-of-range index reads record 0. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042D940)
char *__thiscall f_0042D940(char *this, unsigned int index)
{
    if (index >= *(unsigned int *)(this + 8))
        index = 0;
    return *(char **)this + *(int *)(this + 0xc) * index * 0x18;
}
