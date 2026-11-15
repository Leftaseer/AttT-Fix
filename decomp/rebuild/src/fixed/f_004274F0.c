/* 0x004274F0: copies 0xC-byte records backwards, from [begin, end) to the area ending at dst (the classic
 * "move a range towards its front" loop of an erase). */
#include "auto_pre.h"

DECOMP(004274F0)
void __cdecl f_004274F0(char *begin, char *end, char *dst)
{
    while (end != begin) {
        end -= 0xc;
        dst -= 0xc;
        *(unsigned int *)dst = *(unsigned int *)end;
        *(unsigned int *)(dst + 4) = *(unsigned int *)(end + 4);
        *(unsigned int *)(dst + 8) = *(unsigned int *)(end + 8);
    }
}
