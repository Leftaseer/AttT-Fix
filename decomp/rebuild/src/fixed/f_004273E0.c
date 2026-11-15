/* 0x004273E0: the byte count/flag byte of a map node (+0x31). */
/* @conv 0 */
#include "auto_pre.h"

DECOMP(004273E0)
int __cdecl f_004273E0(void *node)
{
    return (int)node + 0x31;
}
