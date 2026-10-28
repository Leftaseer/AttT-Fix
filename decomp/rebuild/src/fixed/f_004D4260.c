/* 0x004D4260: the top byte of the dword passed in ECX (read back from where 'push ecx' put it) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004D4260)
unsigned int __thiscall f_004D4260(unsigned int value)
{
    return value >> 24;
}
