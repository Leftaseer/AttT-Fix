/* 0x004AC740: copies three floats (+0x98, +0x9c, +0xa0) to +0x128, +0x13c, +0x150 and sets the flags at
 * +0xa4 and +0x1ac; returns EAX as it came.  The decompiler also wrote a dword at the unaligned +0x129 (its view
 * of overlapping fields), a store the machine code does not make, which clobbered the float at +0x128. */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 004AC740 custom */

DECOMP(004AC740)
unsigned int __cdecl f_004AC740(void *this, unsigned int eax)
{
    *(unsigned char *)((char *)this + 0xa4) = 0;
    *(float *)((char *)this + 0x128) = *(float *)((char *)this + 0x98);
    *(unsigned char *)((char *)this + 0x1ac) = 1;
    *(float *)((char *)this + 0x13c) = *(float *)((char *)this + 0x9c);
    *(float *)((char *)this + 0x150) = *(float *)((char *)this + 0xa0);
    return eax;
}
