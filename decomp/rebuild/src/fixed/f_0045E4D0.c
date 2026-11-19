/* 0x0045E4D0: creates the 0x374-byte CNpc (0x00533E30) from the script table, the registry [0x006C8E40] and this
 * object.  When the world screen is up ([world +0x40] of 0x006C88D8 is not zero) the npc is linked into this
 * object's +0x1B4 list (0x0045E230, which also sets the npc's +0x1BC back-pointer) and handed to the world
 * (0x005AD210).  Otherwise the pose comes from 0x004ACE70 (the floats at +0x30, +0x34 and +0x38): the npc's
 * +0x64/+0x68/+0x6C floats move down to +0x58/+0x5C/+0x60, the pose floats take their place, +0x70 and +0x80 are
 * raised, +0x1BC is cleared, the parent's point ([[this +0x1BC] + 0x78]) plus this object's +0x78 are added to the
 * npc's +0x78, a {list, first, npc} node (0x005AD6C0) is prepended to the list at [this +0x204] (grown by
 * 0x004E0EF0 with 1) and the npc's +0x1FC goes to the registry through 0x00425390. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C char d_006C88D8[], d_006C8E40[];
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                   /* operator new */
DECOMP_C void *__thiscall sub_00533E30(void *self, void *tbl, void *a2, void *a3);
DECOMP_C void __thiscall sub_0045E230(void *self, void *npc);
DECOMP_C void __thiscall sub_005AD210(void *self, void *npc);
DECOMP_C void *__thiscall sub_004ACE70(void *self, void *pose);
DECOMP_C void *__stdcall sub_005AD6C0(void *list, void *first, void **obj);
DECOMP_C void __thiscall sub_004E0EF0(void *self, int count);
DECOMP_C void __thiscall sub_00425390(void *self, void *obj);

DECOMP(0045E4D0)
void __thiscall f_0045E4D0(void *self, void *tbl)
{
    char *this = (char *)self;
    char *mem = (char *)sub_005E3EAE(0x374);
    char *npc = mem ? (char *)sub_00533E30(mem, tbl, *(void **)d_006C8E40, self) : 0;
    char *world = *(char **)d_006C88D8;

    if (world[0x40]) {
        sub_0045E230(this, npc);
        sub_005AD210(world, npc);
        return;
    }
    {
        float pose[15];
        unsigned int old0, old1, old2;
        char *list, *node;
        void *first;

        sub_004ACE70(npc, pose);
        old0 = *(unsigned int *)(npc + 0x64);
        old1 = *(unsigned int *)(npc + 0x68);
        old2 = *(unsigned int *)(npc + 0x6c);
        *(float *)(npc + 0x64) = pose[0x30 / 4];
        *(unsigned int *)(npc + 0x58) = old0;
        *(float *)(npc + 0x68) = pose[0x34 / 4];
        *(unsigned int *)(npc + 0x5c) = old1;
        *(float *)(npc + 0x6c) = pose[0x38 / 4];
        *(unsigned int *)(npc + 0x60) = old2;
        npc[0x70] = 1;
        *(float *)(npc + 0x78) = *(float *)(*(char **)(this + 0x1bc) + 0x78) + *(float *)(this + 0x78) +
            *(float *)(npc + 0x78);
        npc[0x80] = 1;
        *(void **)(npc + 0x1bc) = 0;
        list = *(char **)(this + 0x204);
        first = *(void **)(list + 4);
        node = (char *)sub_005AD6C0(list, first, (void **)&npc);
        sub_004E0EF0(this + 0x200, 1);
        *(void **)(list + 4) = node;
        *(void **)first = node;
        sub_00425390(*(void **)d_006C8E40, npc + 0x1fc);
    }
}
