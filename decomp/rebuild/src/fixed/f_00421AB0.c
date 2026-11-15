/* 0x00421AB0: copy constructor: the strings at +0, +0xAC and +0xC8 by the MSVCP80 string copy constructor, the blocks
 * at +0x1C and +0x64 by 0x00421150.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *__thiscall sub_00421150(void *self, const void *src);

DECOMP(00421AB0)
void *__thiscall f_00421AB0(void *self, const void *src)
{
    char *s = (char *)self, *o = (char *)src;
    imp_00607334(s, o);
    sub_00421150(s + 0x1c, o + 0x1c);
    sub_00421150(s + 0x64, o + 0x64);
    imp_00607334(s + 0xac, o + 0xac);
    imp_00607334(s + 0xc8, o + 0xc8);
    return s;
}
