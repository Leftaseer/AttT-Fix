/* 0x00486280: copies the incoming by-value string, forwards that copy as the by-value
 * string argument of 00485BA0, and destroys the incoming string. */
/* @conv ECX 36 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[7];
} String_00486280;

DECOMP_C void __thiscall sub_00485BA0(void *self, String_00486280 value);
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(00486280)
void __thiscall f_00486280(void *this, String_00486280 value,
                           unsigned int unused8, unsigned int unused9)
{
    String_00486280 local_string;

    imp_00607334(&local_string, &value);
    sub_00485BA0(this, local_string);
    imp_00607330(&value);
}
