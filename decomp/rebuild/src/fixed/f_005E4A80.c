/* 0x005E4A80: the initializer-table walk of __cinit: both bounds are the absolute address 0x00698FF4, i.e.
 * the table of static initializers is empty in this executable, so the loop never runs.  (The bounds are
 * link-time constants with no symbol of their own, hence the literal.) */
#include "auto_pre.h"

DECOMP(005E4A80)
void __cdecl f_005E4A80(void)
{
    void (**entry)(void) = (void (**)(void))0x00698FF4;
    void (**end)(void) = (void (**)(void))0x00698FF4;

    for (; entry < end; entry++)
        if (*entry)
            (*entry)();
}
