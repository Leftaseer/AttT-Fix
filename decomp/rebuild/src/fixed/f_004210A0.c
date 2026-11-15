/* 0x004210A0: copy constructor for a record with two strings - the one at +0 and the one at +0x1C by the MSVCP80
 * string copy constructor - and four dwords copied from +0x38, +0x3C, +0x40 and +0x44.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(004210A0)
void *__thiscall f_004210A0(void *self, const void *src)
{
    char *s = (char *)self, *o = (char *)src;
    imp_00607334(s, o);
    imp_00607334(s + 0x1c, o + 0x1c);
    *(int *)(s + 0x38) = *(int *)(o + 0x38);
    *(int *)(s + 0x3c) = *(int *)(o + 0x3c);
    *(int *)(s + 0x40) = *(int *)(o + 0x40);
    *(int *)(s + 0x44) = *(int *)(o + 0x44);
    return s;
}
