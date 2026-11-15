/* 0x0042B620: stores the value at +0x0C (a scene's setting slot). */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042B620)
void __thiscall f_0042B620(void *this, unsigned int value)
{
    *(unsigned int *)((char *)this + 0xc) = value;
}
