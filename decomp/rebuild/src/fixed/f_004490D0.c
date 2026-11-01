/* 0x004490D0: square, rounded to float as the original's fstp dword does */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP(004490D0)
float __cdecl f_004490D0(float param_1)
{
    volatile float r = param_1 * param_1;

    return r;
}
