/* 0x004FCB40: the flat cell index of the point pos (x, y) relative to the cell this points at: y rows of
 * 0x006CA8C4 cells back from it plus x.  The slot at the board (0x006CA8C8, 16-byte entries) of that cell decides
 * whether an odd x keeps its own row (its +8 byte set) or lies one row further back (the staggered rows).  *out only;
 * returns nothing. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_006CA8C4[], d_006CA8C8[];

DECOMP(004FCB40)
void __thiscall f_004FCB40(void *self, unsigned int *out, const int *pos)
{
    int base = *(int *)self;
    int y = pos[1];

    if (*(char *)(base * 16 + 8 + *(char **)d_006CA8C8) == 0 && (pos[0] & 1))
        y++;
    *out = (unsigned int)(base + pos[0] - y * *(int *)d_006CA8C4);
}
