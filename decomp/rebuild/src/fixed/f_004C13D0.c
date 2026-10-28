/* 0x004C13D0: the master volume of the digital driver at 0x6CA498 (Miles AIL_digital_master_volume_level, a
 * float in ST0) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C float (__stdcall *imp_0060786C)(void *) __asm__("__imp__AIL_digital_master_volume_level@4");
DECOMP_C char d_006CA498[];

DECOMP(004C13D0)
float __cdecl f_004C13D0(void)
{
    return imp_0060786C(*(void **)d_006CA498);
}
