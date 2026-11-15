/* 0x00420650: builds the exception object from the string arg 1: the std::exception base is default-built
 * (MSVCR80 IAT 0x6073A4), the vtable 0x00607B18 is stored at +0 and the message at +0xC is copied from the argument
 * by the string copy constructor (MSVCP80 IAT 0x607334).  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607B18[];
DECOMP_C void (__thiscall *imp_006073A4)(void *) __asm__("__imp_??0exception@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(00420650)
void *__thiscall f_00420650(void *self, const void *message)
{
    imp_006073A4(self);
    *(void **)self = d_00607B18;
    imp_00607334((char *)self + 0xc, message);
    return self;
}
