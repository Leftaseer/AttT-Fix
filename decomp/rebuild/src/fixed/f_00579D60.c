/* 0x00579D60: _ctime64 of the time at EAX (an LTCG convention of its own) */
/* @conv EAX 0 */
#include "auto_pre.h"
/* @func 00579D60 custom */
DECOMP_C char * (__cdecl *imp_0060748C)(const long long *) __asm__("__imp___ctime64");

DECOMP(00579D60)
char * __cdecl f_00579D60(const long long *t)
{
    return imp_0060748C(t);
}
