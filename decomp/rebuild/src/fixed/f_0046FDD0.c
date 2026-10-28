/* 0x0046FDD0: realloc with the block in ECX and the size in EAX (an LTCG convention of its own) */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 0046FDD0 custom */
DECOMP_C void * (__cdecl *imp_00607410)(void *, _crtdefs_h_size_t) __asm__("__imp__realloc");

DECOMP(0046FDD0)
void * __cdecl f_0046FDD0(void *block, _crtdefs_h_size_t size)
{
    return imp_00607410(block, size);
}
