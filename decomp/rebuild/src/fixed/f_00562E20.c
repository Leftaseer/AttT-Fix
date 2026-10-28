/* Lua_006C73C0::NextTroop 0x00562E20: the tactic level's next troop (0x50B9A0 on the level at 0xBC) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C undefined4 __thiscall sub_0050B9A0(void *level);

DECOMP(00562E20)
int __thiscall f_00562E20(void *this, void *args)
{
    sub_0050B9A0(*(void **)((char *)this + 0xbc));
    return 0;
}
