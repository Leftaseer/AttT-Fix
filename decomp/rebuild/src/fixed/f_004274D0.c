/* 0x004274D0: swaps the two bytes. */
/* @conv 0 */
#include "auto_pre.h"

DECOMP(004274D0)
void __cdecl f_004274D0(unsigned char *a, unsigned char *b)
{
    unsigned char tmp = *a;
    *a = *b;
    *b = tmp;
}
