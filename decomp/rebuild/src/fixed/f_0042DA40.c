/* 0x0042DA40: element `index` of the pointer vector at +4..+8 (a null vector or an out-of-range index gives 0). */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042DA40)
unsigned int __thiscall f_0042DA40(char *this, unsigned int index)
{
    char *begin = *(char **)(this + 4);

    if (!begin || index >= (unsigned int)(*(int *)(this + 8) - (int)begin) >> 2)
        return 0;
    return ((unsigned int *)begin)[index];
}
