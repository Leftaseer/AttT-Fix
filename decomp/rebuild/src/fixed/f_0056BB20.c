/* 0x0056BB20: lua-method wrapper: reaches the lua object through +8 -> +4 -> +8 and forwards the argument to
 * Lua_006C7460::Enabled (0x5339E0). */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_005339E0(void *self, int arg);

DECOMP(0056BB20)
int __thiscall f_0056BB20(void *this, int arg)
{
    char *o = *(char **)(*(char **)((char *)this + 8) + 4);
    return sub_005339E0(*(void **)(o + 8), arg);
}
