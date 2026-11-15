/* 0x00511B30: moves the creature to board slot arg 1 (16-byte slots: x, y, kind, free at +9, owner at +0xC): while
 * slot this+0x2BC of the global board (0x006CA8C8) still names the creature it is released (owner cleared, free set);
 * the new slot of the board at this+0x3B0's +0x68 takes the creature and its point is sent to 0x004AC940. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { float x, y; unsigned char kind, free; unsigned short pad; void *owner; } Slot_511B30;
DECOMP_C char d_006CA8C8[];
DECOMP_C void __thiscall sub_004AC940(void *self, float x, float z);

DECOMP(00511B30)
void __thiscall f_00511B30(void *self, int slot)
{
    char *c = (char *)self;
    Slot_511B30 *old = (Slot_511B30 *)*(char **)d_006CA8C8 + *(int *)(c + 0x2bc);
    Slot_511B30 *cur;

    if (old->owner == self) {
        old->owner = 0;
        old->free = 1;
    }
    *(int *)(c + 0x2bc) = slot;
    cur = (Slot_511B30 *)*(char **)(*(char **)(c + 0x3b0) + 0x68) + slot;
    cur->owner = self;
    cur->free = 0;
    sub_004AC940(self, cur->x, cur->y);
}
