/* 0x004A2DB0: std::fill of 100-byte records from first to last with *val (strings at +0, +0x28 and +0x48, the floats
 * at +0x1C, +0x20, +0x44 and the byte at +0x24) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");

DECOMP(004A2DB0)
void __cdecl f_004A2DB0(char *first, char *last, char *val)
{
    for (; first != last; first += 100) {
        imp_0060731C(first, val);
        *(float *)(first + 0x1c) = *(float *)(val + 0x1c);
        *(float *)(first + 0x20) = *(float *)(val + 0x20);
        first[0x24] = val[0x24];
        imp_0060731C(first + 0x28, val + 0x28);
        *(float *)(first + 0x44) = *(float *)(val + 0x44);
        imp_0060731C(first + 0x48, val + 0x48);
    }
}
