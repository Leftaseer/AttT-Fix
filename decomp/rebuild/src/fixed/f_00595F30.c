/* CDXUTEditBox::vf8 0x00595F30: focus gained: flags at 6 and 0x118, the current time of the timer 0x59E480
 * (0x59D900) at 0x114 (the caret blink); EAX afterwards is the timer's leftover, 0 here */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C undefined1 * __cdecl sub_0059E480(void);
DECOMP_C float __thiscall sub_0059D900(void *timer);

DECOMP(00595F30)
undefined4 __thiscall f_00595F30(void *this)
{
    *(unsigned char *)((char *)this + 6) = 1;
    *(unsigned char *)((char *)this + 0x118) = 1;
    *(float *)((char *)this + 0x114) = sub_0059D900(sub_0059E480());
    return 0;
}
