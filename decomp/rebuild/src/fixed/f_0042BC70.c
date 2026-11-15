/* 0x0042BC70: a troop slot's click handler: selects the slot kind stored at the item's +0x50. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042BB90(void *self, unsigned int kind);

DECOMP(0042BC70)
void __thiscall f_0042BC70(void *this, char *item)
{
    sub_0042BB90(this, *(unsigned char *)(item + 0x50));
}
