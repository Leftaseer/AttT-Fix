/* 0x00421A50: copies the object arg 1: the string at +0 by its copy constructor (MSVCP80 IAT 0x607334), then the
 * 0x48-byte block at +0x1C by its own copy constructor (0x00421150).  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void *__thiscall sub_00421150(void *self, const void *src);

DECOMP(00421A50)
void *__thiscall f_00421A50(void *self, const void *src)
{
    imp_00607334(self, src);
    sub_00421150((char *)self + 0x1c, (const char *)src + 0x1c);
    return self;
}
