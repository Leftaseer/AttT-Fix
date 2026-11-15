/* 0x00427820: nScript::TableGet::~TableGet: the count at +0xC is cleared and, when the read owns it (+0x14), the
 * Lua stack shrinks by that many (lua_settop with -1 - the count).  The vtable is wound back through 0x00608260 to
 * the base 0x00607CB8 and the object releases itself as an _Object (0x00422000 throws when +4 is still set). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608260[], d_00607CB8[], d_008D122C[];
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);                  /* lua_settop */
DECOMP_C unsigned int __thiscall sub_00422000(void *self);             /* _Object::~_Object */

DECOMP(00427820)
void __thiscall f_00427820(void *this)
{
    char *s = (char *)this;

    *(void **)s = d_00608260;
    if (*(int *)(s + 0xc) > 0) {
        if (s[0x14])
            sub_00402A70(*(void **)d_008D122C, -1 - *(int *)(s + 0xc));
        *(unsigned int *)(s + 0xc) = 0;
    }
    *(void **)s = d_00607CB8;
    sub_00422000(s);
}
