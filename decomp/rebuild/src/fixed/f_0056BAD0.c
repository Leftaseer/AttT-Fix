/* 0x0056BAD0: lua-method wrapper: reaches the lua object through +8 -> +4 -> +8 and forwards the argument to
 * Lua_006C6E50::Height (0x533950, which ignores it). */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00533950(void *self, int arg);

DECOMP(0056BAD0)
int __thiscall f_0056BAD0(void *this, int arg)
{
    char *o = *(char **)(*(char **)((char *)this + 8) + 4);
    return sub_00533950(*(void **)(o + 8), arg);
}
