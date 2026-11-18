/* 0x0054C0D0: asks the callback at +0x1C to fill a temporary string through the object at
 * +0x24, copies the returned string to the caller's output string, and returns that output. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[7];
} String_0054C0D0;

typedef void *(__thiscall *get_string_0054C0D0)(void *self, String_0054C0D0 *out, void *owner);

DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

DECOMP(0054C0D0)
void *__thiscall f_0054C0D0(char *this, void *output)
{
    String_0054C0D0 temporary;
    get_string_0054C0D0 get_string = *(get_string_0054C0D0 *)(this + 0x1c);
    void *result = get_string(*(void **)(this + 0x24), &temporary, this);

    imp_00607334(output, result);
    imp_00607330(&temporary);
    return output;
}
