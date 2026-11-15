/* 0x00427020: the std::logic_error deleting destructor: vtable 0x00607B18, the message string at +0xC is destroyed
 * (MSVCP80 string destructor), then the std::exception base, and the delete when flag bit 0 is set.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607B18[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006073AC)(void *) __asm__("__imp_??1exception@std@@UAE@XZ");
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00427020)
void *__thiscall f_00427020(void *this, unsigned int flags)
{
    char *s = (char *)this;
    *(const void **)s = d_00607B18;
    imp_00607330(s + 0xc);
    imp_006073AC(s);
    if (flags & 1)
        sub_005E3E9C(s);
    return s;
}
