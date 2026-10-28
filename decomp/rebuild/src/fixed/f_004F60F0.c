/* 0x004F60F0: NSound::UnitSoundManager::Update(dt): its four updates, the clock (+0xAC) advances, and numpad 1 / 3
 * held (GetKeyState) turn the volume (+0xB0) down / up by the double at 0x6082A0 (0x004EDD60) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004EECA0(void *self);
DECOMP_C void __thiscall sub_004EDDE0(void *self);
DECOMP_C void __thiscall sub_004F5F00(void *self);
DECOMP_C void __thiscall sub_004F4E20(void *self);
DECOMP_C void __thiscall sub_004EDD60(void *self, float volume);
DECOMP_C char d_006082A0[];
DECOMP_C short (__stdcall *imp_006076D0)(int) __asm__("__imp__GetKeyState@4");

DECOMP(004F60F0)
void __thiscall f_004F60F0(void *this, float dt)
{
    char *s = (char *)this;
    sub_004EECA0(this);
    sub_004EDDE0(this);
    sub_004F5F00(this);
    sub_004F4E20(this);
    *(float *)(s + 0xac) = dt + *(float *)(s + 0xac);
    if (imp_006076D0(0x61) < 0)                    /* VK_NUMPAD1 */
        sub_004EDD60(this, (float)(*(float *)(s + 0xb0) - *(double *)d_006082A0));
    if (imp_006076D0(0x63) < 0)                    /* VK_NUMPAD3 */
        sub_004EDD60(this, (float)(*(float *)(s + 0xb0) + *(double *)d_006082A0));
}
