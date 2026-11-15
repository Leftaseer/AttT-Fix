/* 0x004C1710: NSound::Sound2D vf3: unless the sample is loaded (+8 clear, then the input EAX passes through)
 * marks it started (+9 = 1), sets its loop count and, when the second argument (milliseconds) is 0, starts it
 * from the beginning, otherwise seeks it there and resumes it.  The result of the last AIL call is returned. */
/* @conv EAX,ECX 8 */
/* @func 004C1710 custom */
#include "auto_pre.h"
DECOMP_C int (__stdcall *imp_006078A4)(void *, int) __asm__("__imp__AIL_set_sample_loop_count@8");
DECOMP_C int (__stdcall *imp_00607890)(void *) __asm__("__imp__AIL_start_sample@4");
DECOMP_C int (__stdcall *imp_0060788C)(void *, int) __asm__("__imp__AIL_set_sample_ms_position@8");
DECOMP_C int (__stdcall *imp_00607888)(void *) __asm__("__imp__AIL_resume_sample@4");

DECOMP(004C1710)
int __cdecl f_004C1710(undefined4 in_eax, char *this, int loops, int milliseconds)
{
    if (!this[8])
        return in_eax;
    this[9] = 1;
    imp_006078A4(*(void **)(this + 0x38), loops);
    if (!milliseconds)
        return imp_00607890(*(void **)(this + 0x38));
    imp_0060788C(*(void **)(this + 0x38), milliseconds);
    return imp_00607888(*(void **)(this + 0x38));
}
