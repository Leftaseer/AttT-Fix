/* 0x005540B0: the same destruction as 0x00553C50 for an object passed on the stack */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(005540B0)
void __cdecl f_005540B0(void *p)
{
    char *s = (char *)p + 8;
    if (*(void **)(s + 0x20))
        sub_005E3E9C(*(void **)(s + 0x20));
    *(unsigned int *)(s + 0x20) = 0;
    *(unsigned int *)(s + 0x24) = 0;
    *(unsigned int *)(s + 0x28) = 0;
    imp_00607330(s);
}
