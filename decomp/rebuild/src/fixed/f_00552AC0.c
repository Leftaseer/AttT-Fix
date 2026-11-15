/* 0x00552AC0: NParticleSystem::CParticleSystem::Tick (CUpdateObject slot): ticks the particle system in mode 3. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00551F60(void *self, int mode);

DECOMP(00552AC0)
int __thiscall f_00552AC0(void *this)
{
    return sub_00551F60(this, 3);
}
