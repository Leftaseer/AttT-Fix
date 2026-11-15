/* 0x0042BB90: selects troop slot `kind`: when the hero's class allows it (bit `kind` of the word table 0x6BF684 by the
 * class at +0x1D8 of 0x00425F60's hero), the byte +0x158 takes it, the selection level picture (+0xD0) shows slot
 * `kind`'s picture (+0xDC) moved to its rectangle (+0xD4..) at 0,0, and the soldier / level picture (+0x164) shows
 * the hero-class picture (+0x15C) or the other one (+0x160) at 0,0. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C char d_006BF684[];
DECOMP_C int __stdcall sub_0042BB10(void);

typedef void (__thiscall *vf34_42BB90)(void *self, unsigned int picture);
typedef void (__thiscall *vf6c_42BB90)(void *self, void *rectangle);
typedef void (__thiscall *vf94_42BB90)(void *self, float x, float y);

#define VT(o) (*(void ***)(o))

DECOMP(0042BB90)
void __thiscall f_0042BB90(char *this, unsigned int kind)
{
    unsigned short allowed = ((unsigned short *)d_006BF684)[*(int *)(sub_00425F60() + 0x1d8)];
    char *level, *mark;

    if (!((1u << (kind & 0x1f)) & allowed))
        return;
    *(unsigned char *)(this + 0x158) = (unsigned char)kind;
    level = *(char **)(this + 0xd0);
    ((vf34_42BB90)VT(level)[0xd])(level, *(unsigned int *)(this + 0xdc + kind * 0xc));
    level = *(char **)(this + 0xd0);
    ((vf6c_42BB90)VT(level)[0x1b])(level, this + 0xd4 + kind * 0xc);
    level = *(char **)(this + 0xd0);
    ((vf94_42BB90)VT(level)[0x25])(level, 0.0f, 0.0f);
    mark = *(char **)(this + 0x164);
    if (*(unsigned char *)(this + 0x158) == (unsigned char)sub_0042BB10())
        ((vf34_42BB90)VT(mark)[0xd])(mark, *(unsigned int *)(this + 0x15c));
    else
        ((vf34_42BB90)VT(mark)[0xd])(mark, *(unsigned int *)(this + 0x160));
    mark = *(char **)(this + 0x164);
    ((vf94_42BB90)VT(mark)[0x25])(mark, 0.0f, 0.0f);
}
