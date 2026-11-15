/* 0x00420C80: copies the exception object arg 1: the std::exception base (MSVCR80's copy constructor), then the
 * vtable 0x00607B18 at +0 and a copy of the string at +0xC.  Returns this.  (The original's exception frame only
 * watches this copy.) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607B18[];
DECOMP_C void (__thiscall *imp_006073BC)(void *, const void *) __asm__("__imp_??0exception@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(00420C80)
void *__thiscall f_00420C80(void *self, void *src)
{
    imp_006073BC(self, src);
    *(void **)self = d_00607B18;
    imp_00607334((char *)self + 0xc, (char *)src + 0xc);
    return self;
}
