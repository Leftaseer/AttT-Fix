/* 0x00553C50: destroys the object at this+8: frees its buffer at +0x20 (zeroing +0x20..+0x28), then the std::string */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00553C50)
void __thiscall f_00553C50(void *this)
{
    char *s = (char *)this + 8;
    if (*(void **)(s + 0x20))
        sub_005E3E9C(*(void **)(s + 0x20));
    *(unsigned int *)(s + 0x20) = 0;
    *(unsigned int *)(s + 0x24) = 0;
    *(unsigned int *)(s + 0x28) = 0;
    imp_00607330(s);
}
