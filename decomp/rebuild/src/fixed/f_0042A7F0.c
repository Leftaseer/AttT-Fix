/* 0x0042A7F0: steps the animation by dt (the base update 0x004AD110, with EAX as it came) and passes dt on to slot 4
 * of the driven object at +0x1C4; its result is returned. */
/* @conv ECX,EAX 4 */
/* @func 0042A7F0 custom */
#include "auto_pre.h"

DECOMP_C unsigned int __cdecl sub_004AD110(void *self, unsigned int eax, float dt);
typedef int (__thiscall *vf_42A7F0)(void *self, float dt);

DECOMP(0042A7F0)
int __cdecl f_0042A7F0(char *this, unsigned int in_eax, float dt)
{
    char *driven;

    sub_004AD110(this, in_eax, dt);
    driven = *(char **)(this + 0x1c4);
    return ((vf_42A7F0)(*(void ***)driven)[4 / 4])(driven, dt);
}
