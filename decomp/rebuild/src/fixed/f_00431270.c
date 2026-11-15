/* 0x00431270: sends the raw state of the span to the stream: the two dwords at +4 and +8 (each written as four
 * bytes), then the buffer at +0 with the count from +4.  AL is set on success (the rest of the result is what
 * the stream's write returned). */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *(__thiscall *imp_006071B0)(void *, const void *, int) __asm__("__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z");

DECOMP(00431270)
unsigned int __thiscall f_00431270(char *this, void *stream)
{
    void *result;

    imp_006071B0(stream, this + 4, 4);
    imp_006071B0(stream, this + 8, 4);
    result = imp_006071B0(stream, *(void **)this, *(int *)(this + 4));
    return ((unsigned int)result & 0xffffff00u) | 1;      /* mov al,1 */
}
