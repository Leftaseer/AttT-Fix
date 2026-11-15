/* 0x0042E750: _time64(EAX): returns the __time64_t EAX points at (or the current time when EAX is null) */
/* @conv EAX 0 */
/* @func 0042E750 custom */
#include "auto_pre.h"
DECOMP_C __int64 (__cdecl *imp_006073EC)(__int64 *t) __asm__("__imp___time64");

DECOMP(0042E750)
__int64 __cdecl f_0042E750(__int64 *in_eax)
{
    return imp_006073EC(in_eax);
}
