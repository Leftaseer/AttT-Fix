/* 0x0053A620: CTacticLevel's third level-component name (the string slot +0x254 of the object in ECX): the 28-byte
 * string passed by value (the second stack argument; the first one is ignored) is assigned over it and destroyed
 * again, as the caller's temporaries expect.  Called by the tactic level set-up 0x00543820. */
/* @conv ECX 32 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_53A620;
DECOMP_C void *(__thiscall *imp_0060731C)(void *self, const void *src) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *self) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0053A620)
void __thiscall f_0053A620(void *this, int unused, Str_53A620 value)
{
    imp_0060731C((char *)this + 0x254, &value);
    imp_00607330(&value);
}
