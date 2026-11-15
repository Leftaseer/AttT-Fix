/* 0x00431100: reads the span back from the stream - the capacity from +4, the size from +8, then asks the
 * allocator/setter at +0 to reserve that many bytes before the payload lands in the buffer.  AL=1 marks the
 * stream operation as successful; the upper bytes of the result keep the stream reference. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *(__thiscall *imp_006071A0)(void *, char *, int) __asm__("__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z");
DECOMP_C void __thiscall sub_004310A0(void *self, unsigned int count);

DECOMP(00431100)
unsigned int __thiscall f_00431100(char *this, void *stream)
{
    void *result;

    imp_006071A0(stream, this + 4, 4);
    imp_006071A0(stream, this + 8, 4);
    sub_004310A0(this, *(unsigned int *)(this + 8));
    result = imp_006071A0(stream, *(void **)this, *(int *)(this + 4));
    return ((unsigned int)result & 0xffffff00u) | 1;
}
