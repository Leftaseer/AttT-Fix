/* 0x0042B720: looks for the (first, second) pair in the table whose keys are at 0x006C8858 and whose second values
 * are at 0x006C885C (d_006BF630 entries): a matching first key alone matches when it is 0, otherwise the second
 * value must match too. Returns the index or -1. */
#include "auto_pre.h"

DECOMP_C char d_006C8858[], d_006C885C[];
DECOMP_C int d_006BF630;

DECOMP(0042B720)
int __cdecl f_0042B720(unsigned int first, unsigned int second)
{
    int count = d_006BF630;
    int i;

    for (i = 0; i < count; i++) {
        if (((unsigned int *)d_006C8858)[2 * i] == first) {
            if (first == 0)
                return i;
            if (((unsigned int *)d_006C885C)[2 * i] == second)
                return i;
        }
    }
    return -1;
}
