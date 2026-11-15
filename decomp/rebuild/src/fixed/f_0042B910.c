/* 0x0042B910: the CArmyScreenScene destructor: puts the scene's vtables in place, releases the eleven troop slots at
 * +0x170, the buttons and pictures (+0x94/+0x98/+0x9C, +0x88, +0xA4, +0xD0, the selection level pictures +0xDC,
 * +0x10C, +0x130, +0x148, +0x154, the soldier / level pictures +0x15C, +0x160 and the denied places mark +0x16C),
 * switches +0x74 back to the CScene vtable and runs the base destructor 0x004B2010. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B2010(void *self);
DECOMP_C char d_00608848[], d_00608864[], d_0060886C[], d_0060888C[];

typedef void (__thiscall *vf0_42B910)(void *self, int freeing);

#define VT(o) (*(void ***)(o))

static void release_42B910(char *s, unsigned int offset)
{
    void *object = *(void **)(s + offset);
    if (object) {
        ((vf0_42B910)VT(object)[0])(object, 1);
        *(void **)(s + offset) = 0;
    }
}

DECOMP(0042B910)
void __thiscall f_0042B910(char *this)
{
    int i;

    *(void **)this = d_0060888C;
    *(void **)(this + 4) = d_0060886C;
    *(void **)(this + 0x74) = d_00608864;
    for (i = 0; i < 11; i++) {
        void *object = *(void **)(this + 0x170 + 4 * i);
        if (object)
            ((vf0_42B910)VT(object)[0])(object, 1);     /* the troop slots are released but left in place */
    }
    release_42B910(this, 0x94);
    release_42B910(this, 0x98);
    release_42B910(this, 0x9c);
    release_42B910(this, 0x88);
    release_42B910(this, 0xa4);
    release_42B910(this, 0xdc);
    release_42B910(this, 0x10c);
    release_42B910(this, 0x130);
    release_42B910(this, 0x148);
    release_42B910(this, 0x154);
    release_42B910(this, 0xd0);
    release_42B910(this, 0x15c);
    release_42B910(this, 0x160);
    release_42B910(this, 0x16c);
    *(void **)(this + 0x74) = d_00608848;
    sub_004B2010(this);
}
