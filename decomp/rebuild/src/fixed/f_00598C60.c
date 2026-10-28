/* CDXUTCheckBox::vf12 0x00598C60: toggles the box: virtual function 0x50 (SetChecked) with the negated state at
 * 0x15C and 1 (from input) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00598C60)
undefined4 __thiscall f_00598C60(void *this)
{
    return ((undefined4 (__thiscall *)(void *, undefined4, undefined4))(*(void ***)this)[0x50 / 4])(
        this, *(unsigned char *)((char *)this + 0x15c) == 0, 1);
}
