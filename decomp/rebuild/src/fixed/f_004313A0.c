/* 0x004313A0: writes the span-array header (+4, +8), then every 12-byte record's size,
 * payload, and keyed field.  AL is set; the rest of EAX is the last header write result for
 * an empty array and this+8 after a nonempty one. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *(__thiscall *imp_006071B0)(void *, const void *, int) __asm__("__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z");

DECOMP(004313A0)
unsigned int __thiscall f_004313A0(char *this, void *stream)
{
    unsigned int result;
    unsigned int i, count;

    imp_006071B0(stream, this + 4, 4);
    result = (unsigned int)imp_006071B0(stream, this + 8, 4);
    for (i = 0; i < *(unsigned int *)(this + 8); i++) {
        char *record = *(char **)this + i * 0xc;

        imp_006071B0(stream, record + 4, 4);
        imp_006071B0(stream, record + 8, 4);
        imp_006071B0(stream, *(void **)record, *(unsigned int *)(record + 4));
        result = (unsigned int)(this + 8);
    }
    return (result & 0xffffff00u) | 1;
}
