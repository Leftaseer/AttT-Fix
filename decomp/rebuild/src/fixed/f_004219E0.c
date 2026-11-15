/* 0x004219E0: copy-constructs the record at arg 1 from arg 2 - only when arg 1 is not null: the string at +0 by the
 * MSVCP80 copy constructor and the four dwords at +0x1C..+0x28 (a cdecl helper returning nothing). */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");

DECOMP(004219E0)
void __cdecl f_004219E0(void *self, const void *src)
{
    char *s = (char *)self, *o = (char *)src;
    if (!s)
        return;
    imp_00607334(s, o);
    *(int *)(s + 0x1c) = *(int *)(o + 0x1c);
    *(int *)(s + 0x20) = *(int *)(o + 0x20);
    *(int *)(s + 0x24) = *(int *)(o + 0x24);
    *(int *)(s + 0x28) = *(int *)(o + 0x28);
}
