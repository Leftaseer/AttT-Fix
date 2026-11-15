/* 0x004205E0: builds the message of a std::exception through MSVCR80's exception constructor (IAT 0x6073B4) from
 * the pointer argument, then stamps the std::bad_alloc vtable 0x00607B0C over it; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607B0C[];
DECOMP_C void (__thiscall *imp_006073B4)(void *, const char *const *)
    __asm__("__imp_??0exception@std@@QAE@ABQBD@Z");

DECOMP(004205E0)
void *__thiscall f_004205E0(void *this, const char *const *message)
{
    imp_006073B4(this, &message);
    *(const void **)this = d_00607B0C;
    return this;
}
