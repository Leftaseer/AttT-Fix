/* 0x00421B50: copy constructor: the strings at +0 and +0xB4 by the MSVCP80 string copy constructor, the blocks at
 * +0x1C, +0x68 and +0xD0 by 0x00421150, and the floats at +0x64 and +0xB0.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *__thiscall sub_00421150(void *self, const void *src);

DECOMP(00421B50)
void *__thiscall f_00421B50(void *self, const void *src)
{
    char *s = (char *)self, *o = (char *)src;
    imp_00607334(s, o);
    sub_00421150(s + 0x1c, o + 0x1c);
    *(float *)(s + 0x64) = *(float *)(o + 0x64);
    sub_00421150(s + 0x68, o + 0x68);
    *(float *)(s + 0xb0) = *(float *)(o + 0xb0);
    imp_00607334(s + 0xb4, o + 0xb4);
    sub_00421150(s + 0xd0, o + 0xd0);
    return s;
}
