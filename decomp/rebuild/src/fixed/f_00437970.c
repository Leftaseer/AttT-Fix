/* 0x00437970: an nScript object the script handle arg 1 names: the vtable 0x00608260 at +0 with nothing at +4, the
 * handle at +8, +0xC = the Lua state's (0x008D122C) stack top (0x00402A60, kept to be restored), +0x10 = 0 and the
 * byte arg 2 at +0x14.  Returns the object.  (The original registers an exception frame only to free the object when
 * the state is refilled; nothing here throws.) */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_00608260[], d_008D122C[];
DECOMP_C int __cdecl sub_00402A60(void *L);                            /* lua_gettop */

DECOMP(00437970)
void *__thiscall f_00437970(void *self, void *handle, int flag)
{
    char *c = (char *)self;

    *(void **)(c + 4) = 0;
    *(void **)c = d_00608260;
    *(void **)(c + 8) = handle;
    *(int *)(c + 0xc) = sub_00402A60(*(void **)d_008D122C);
    *(int *)(c + 0x10) = 0;
    c[0x14] = (char)flag;
    return c;
}
