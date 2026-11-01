/* 0x00481000: stores the larger of the two 16-bit ids at this+0x20, then scans the words of the 16-byte table entry
 * this[1][min<<4] from +4 to +8 for one equal to that id; the scan's result is unused, so the optimizer dropped the
 * whole loop (a dead load may fault); the volatile keeps the reads, as in the original */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00481000)
void __thiscall f_00481000(void *this, undefined4 param_1, undefined4 param_2)
{
    unsigned short lo = (unsigned short)param_1, hi = (unsigned short)param_2;
    char *node;
    volatile unsigned short *p, *end;

    if (hi < lo) {
        unsigned short t = hi;

        hi = lo;
        lo = t;
    }
    *(unsigned short *)((char *)this + 0x20) = hi;
    node = *(char **)((char *)this + 4) + ((unsigned int)lo << 4);
    p = (volatile unsigned short *)*(void **)(node + 4);
    end = (volatile unsigned short *)*(void **)(node + 8);
    while (p != end && *p != hi)
        p += 2;
}
