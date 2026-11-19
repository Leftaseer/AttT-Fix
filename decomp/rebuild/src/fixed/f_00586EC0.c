/* 0x00586EC0: nGUI::Rect from a script call (argument: the context whose int at +0x10 is the Lua stack base): the
 * base constructor 0x00582350 and the vtables 0x0061E864 / +0x214 0x0061E85C, then the Lua numbers base+1 .. base+4
 * become the outline's x, y, w and h and base+5 its colour, truncated to an int through a long long (0x00402DE0 with
 * the state 0x008D122C); passed to 0x00586BA0.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00582350(void *self);
DECOMP_C float __cdecl sub_00402DE0(void *L, int idx);                  /* lua_tonumber */
DECOMP_C void __thiscall sub_00586BA0(void *self, float x, float y, float w, float h, unsigned int color);
DECOMP_C char d_008D122C[], d_0061E864[], d_0061E85C[];

DECOMP(00586EC0)
void *__thiscall f_00586EC0(void *self, void *ctx)
{
    char *s = (char *)self;
    void *L = *(void **)d_008D122C;
    int base;
    sub_00582350(s);
    *(char **)s = d_0061E864;
    *(char **)(s + 0x214) = d_0061E85C;
    base = *(int *)((char *)ctx + 0x10);
    sub_00586BA0(s,
                 sub_00402DE0(L, base + 1),
                 sub_00402DE0(L, base + 2),
                 sub_00402DE0(L, base + 3),
                 sub_00402DE0(L, base + 4),
                 (unsigned int)(int)(long long)sub_00402DE0(L, base + 5));
    return s;
}
