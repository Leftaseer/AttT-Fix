/* 0x004CCFE0: StaticObjectManager::Render: renders through 0x4CCEE0 with the manager at +0x38 and the this pointer
 * with its low byte cleared (the original zeroes the first byte of a stack copy and passes all four). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_004CCEE0(void *self, unsigned int arg);

DECOMP(004CCFE0)
int __thiscall f_004CCFE0(char *this)
{
    return sub_004CCEE0(this + 0x38, (unsigned int)this & 0xFFFFFF00);
}
