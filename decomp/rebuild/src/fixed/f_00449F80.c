/* 0x00449F80: CEngine::SetActive applies the saved master volume when active (or zero when
 * inactive), then resumes the game timer or clears its running flag. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004E4200(void *self);
DECOMP_C char d_006CA494[], d_006CA498[];
DECOMP_C void (__stdcall *imp_00607868)(void *driver, float volume) __asm__("__imp__AIL_set_digital_master_volume_level@8");

DECOMP(00449F80)
void __thiscall f_00449F80(char *this, unsigned char active)
{
    char *timer;

    imp_00607868(*(void **)d_006CA498, active ? *(float *)d_006CA494 : 0.0f);
    timer = *(char **)(this + 0x7c);
    if (active)
        sub_004E4200(timer + 8);
    else
        timer[0x18] = 0;
}
