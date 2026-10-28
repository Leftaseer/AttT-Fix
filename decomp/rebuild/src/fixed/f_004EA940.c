/* TrAppearHeroPlayAnimSound::Update 0x004EA940: the base update (CRenderObject3D::Update 0x4AD110, this in ECX
 * and a register argument in EAX passed on), then the float of virtual function 0x80 stored at 0x1C8; what EAX
 * holds after that float call is its leftover, 0 here */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 004EA940 custom */
DECOMP_C undefined4 __cdecl sub_004AD110(void *self, undefined4 eax, float dt);

DECOMP(004EA940)
undefined4 __cdecl f_004EA940(void *this, undefined4 eax, float dt)
{
    sub_004AD110(this, eax, dt);
    *(float *)((char *)this + 0x1c8) = ((float (__thiscall *)(void *))(*(void ***)this)[0x80 / 4])(this);
    return 0;
}
