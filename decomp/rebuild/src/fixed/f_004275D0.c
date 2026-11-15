/* 0x004275D0: the pointer at +4 plus 4. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004275D0)
void *__thiscall f_004275D0(void *this)
{
    return *(char **)((char *)this + 4) + 4;
}
