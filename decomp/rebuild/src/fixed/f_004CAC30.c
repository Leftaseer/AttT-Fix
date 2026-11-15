/* 0x004CAC30: assigns the by-value string argument to the string at +0x1E8 and destroys the argument, as the
 * owner of a by-value std::string parameter does. */
/* @conv ECX 28 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4CAC30;                        /* std::string, 28 bytes */
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(004CAC30)
void __thiscall f_004CAC30(char *this, Str_4CAC30 value)
{
    imp_0060731C(this + 0x1e8, &value);
    imp_00607330(&value);
}
