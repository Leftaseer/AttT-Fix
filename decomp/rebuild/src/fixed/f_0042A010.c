/* 0x0042A010: the constructor of a string-headed sound object: the std::string at +0 is default-built and assigned
 * the name passed by value on the stack (its 0x1C bytes are the first argument), the two dwords that follow it go to
 * +0x1C/+0x20, and the by-value temporary is destroyed. Returns this. */
/* @conv ECX 36 */
#include "auto_pre.h"
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_0060731C)(void *, void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

typedef struct { unsigned int raw[7]; } StrByValue;

DECOMP(0042A010)
void *__thiscall f_0042A010(char *this, StrByValue name, unsigned int a, unsigned int b)
{
    imp_006071E0(this);
    imp_0060731C(this, &name);
    *(unsigned int *)(this + 0x1c) = a;
    *(unsigned int *)(this + 0x20) = b;
    imp_00607330(&name);
    return this;
}
