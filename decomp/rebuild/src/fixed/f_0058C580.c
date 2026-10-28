/* 0x0058C580: ChooseHero::Update: the base update (0x004AD110, with EAX as it came); when it is the one that ended
 * the choice (+0x8C set before, clear after) both heroes' models (+0x1C4, +0x1C8) get 0x0058C390; then both models'
 * vf04(dt), returning the second's result */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"
/* @func 0058C580 custom */
DECOMP_C unsigned int __cdecl sub_004AD110(void *self, unsigned int eax, float dt);
DECOMP_C unsigned int __thiscall sub_0058C390(void *self);
typedef unsigned int (__thiscall *vf04_58C580)(void *self, float dt);

DECOMP(0058C580)
unsigned int __cdecl f_0058C580(void *this, unsigned int eax, float dt)
{
    char *s = (char *)this;
    void **m;
    if (s[0x8c]) {
        sub_004AD110(this, eax, dt);
        if (!s[0x8c]) {
            sub_0058C390(*(void **)(s + 0x1c4));
            sub_0058C390(*(void **)(s + 0x1c8));
        }
    } else
        sub_004AD110(this, eax, dt);
    m = *(void ***)(s + 0x1c4);
    ((vf04_58C580)(*(void ***)m)[1])(m, dt);
    m = *(void ***)(s + 0x1c8);
    return ((vf04_58C580)(*(void ***)m)[1])(m, dt);
}
