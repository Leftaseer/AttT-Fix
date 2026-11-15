/* 0x005360F0: Town::~Town: the vftable becomes 0x615A3C; when the world (0x6C88D8) has a captured town (+0x40) the
 * town leaves the world's list (0x005ADCD0); the object at +0x1F8 is closed (vf 6C) and the banner at +0x1F4 is
 * released (refcounted), then the base ScriptableRenderObject3D is destroyed (0x005B4050). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_005ADCD0(void *self, void *town);
DECOMP_C void __thiscall sub_005B4050(void *self);
DECOMP_C char d_00615A3C[], d_006C88D8[];
typedef void (__thiscall *v6C_5360F0)(void *self);
typedef void (__thiscall *rel_5360F0)(void *self, int flag);

DECOMP(005360F0)
void __thiscall f_005360F0(char *this)
{
    char *world = *(char **)d_006C88D8;
    void *o, *banner;

    *(char **)this = d_00615A3C;
    if (world[0x40])
        sub_005ADCD0(world, this);
    o = *(void **)(this + 0x1f8);
    if (o)
        ((v6C_5360F0)(*(void ***)o)[0x6c / 4])(o);
    banner = *(void **)(this + 0x1f4);
    if (banner && !--((unsigned int *)banner)[1])
        ((rel_5360F0)(*(void ***)banner)[0])(banner, 1);
    sub_005B4050(this);
}
