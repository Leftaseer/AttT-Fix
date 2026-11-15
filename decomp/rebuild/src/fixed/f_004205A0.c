/* 0x004205A0: stores two floats (a 2D point/vector) through this, as arguments 2 and 3 */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(004205A0)
void *__thiscall f_004205A0(void *this, float x, float y)
{
    *(float *)this = x;
    *(float *)((char *)this + 4) = y;
    return this;
}
