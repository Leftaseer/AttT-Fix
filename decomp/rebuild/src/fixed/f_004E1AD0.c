/* 0x004E1AD0: nTime::TimeManager::Update (CUpdateObject slot): the frame time goes to the base update (0x00424D90) and
 * to the time tick (0x004E1350); then the clock at +0x3C has its two counters (+0x50, +0x54) formatted as "%02u:%02u"
 * (0x612658) by sprintf (0x6073D0) into a scratch buffer, whose contents are dropped. */
/* @conv EAX,ECX 4 */
/* @func 004E1AD0 custom */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00424D90(void *self, unsigned int eax_in, float dt);
DECOMP_C void __cdecl sub_004E1350(void *self, unsigned int edx_in, float dt);
DECOMP_C char d_00612658[];
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");

DECOMP(004E1AD0)
void __cdecl f_004E1AD0(undefined4 in_eax, char *this, float dt)
{
    char buf[0x100];
    char *clock;
    sub_00424D90(this, in_eax, dt);
    sub_004E1350(this, 0, dt);
    clock = *(char **)(this + 0x3c);
    imp_006073D0(buf, d_00612658, *(unsigned int *)(clock + 0x50), *(unsigned int *)(clock + 0x54));
}
