/* 0x00593DE0: marks the control (0x118) and stores the current time of the timer 0x59E480 gives
 * (0x59D900, a float) at 0x114; what EAX holds after it is the timer's leftover, 0 here */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C undefined1 * __cdecl sub_0059E480(void);
DECOMP_C float __thiscall sub_0059D900(void *timer);

DECOMP(00593DE0)
undefined4 __thiscall f_00593DE0(void *this)
{
    *(unsigned char *)((char *)this + 0x118) = 1;
    *(float *)((char *)this + 0x114) = sub_0059D900(sub_0059E480());
    return 0;
}
