/* 0x004277B0: nScript::TableGet::TableGet(L, table, count, owns): the vtable 0x00608260 at +0, nothing at +4, the
 * table handle at +8, the index base at +0xC, the stack depth above the base at +0x10 (arg 2 values were pushed by
 * the caller) and the ownership byte arg 3 at +0x14.  Returns the object. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_00608260[], d_008D122C[];
DECOMP_C int __cdecl sub_00402A60(void *L);                            /* lua_gettop */

DECOMP(004277B0)
void *__thiscall f_004277B0(void *this, void *table, int count, unsigned char owns)
{
    char *s = (char *)this;

    *(void **)s = d_00608260;
    *(void **)(s + 4) = 0;
    *(void **)(s + 8) = table;
    *(int *)(s + 0xc) = count;
    *(int *)(s + 0x10) = sub_00402A60(*(void **)d_008D122C) - count;
    s[0x14] = (char)owns;
    return s;
}
