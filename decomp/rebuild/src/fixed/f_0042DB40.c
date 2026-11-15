/* 0x0042DB40: per-frame update of a flying projectile: refreshes its world transform (0x004AC890), picks the mesh
 * slot from the owner's (+0x2BC) current pose index (+0x2D0) clamped to the mesh vector (+0x1C8/+0x1CC), copies the
 * owner's transform (+0x168, 16 dwords) over the kept one (+0x214) and draws the mesh (0x00474BC0), passing the
 * owner's info (+0x220 -> +0x1C4) model ids +0x1D8 / +0x1EC while not flying - in flight (+0x2C0) the kept transform
 * is drawn bare. Then the trail (+0x2C8) continues through its vtable entry 2, whose result is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"

typedef void *(__thiscall *vf2_42DB40)(void *self);

DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C void __thiscall sub_00474BC0(void *self, void *matrix, int textured, unsigned int a, unsigned int b);

DECOMP(0042DB40)
void *__thiscall f_0042DB40(void *self)
{
    char *s = (char *)self;
    char *owner;
    char *begin;
    unsigned int index;
    void *mesh;
    void *trail;

    sub_004AC890(self);
    owner = *(char **)(s + 0x2bc);
    index = *(unsigned int *)(owner + 0x2d0);
    begin = *(char **)(s + 0x1c8);
    if (begin == 0)
        index = 0xffffffff;
    else {
        int count = (int)(*(char **)(s + 0x1cc) - begin) >> 2;
        if (index >= (unsigned int)count)
            index = count - 1;
    }
    mesh = *(void **)(begin + index * 4);
    if (s[0x2c0] == 0) {
        char *info = *(char **)(*(char **)(owner + 0x220) + 0x1c4);
        __builtin_memcpy(s + 0x214, owner + 0x168, 0x40);
        sub_00474BC0(mesh, s + 0x214, 1, *(unsigned int *)(info + 0x1d8), *(unsigned int *)(info + 0x1ec));
    } else
        sub_00474BC0(mesh, s + 0x214, 0, 0, 0);
    trail = *(void **)(s + 0x2c8);
    return ((vf2_42DB40)(*(void ***)trail)[2])(trail);
}
