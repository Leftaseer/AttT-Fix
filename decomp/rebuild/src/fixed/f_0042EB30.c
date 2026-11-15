/* 0x0042EB30: the deleting destructor of a std::string: ~basic_string, then operator delete when bit 0 of the flag
 * is set; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607330)(void *self)
    __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(0042EB30)
void *__thiscall f_0042EB30(void *this, unsigned char flag)
{
    imp_00607330(this);
    if (flag & 1)
        sub_005E3E9C(this);
    return this;
}
