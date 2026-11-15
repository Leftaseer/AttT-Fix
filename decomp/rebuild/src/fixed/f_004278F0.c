/* 0x004278F0: the callback a script hands its own number at +0x94 to: an nScript handle (as 0x004278C0 builds it)
 * lives across pushing that float onto the engine's Lua state (0x008D122C), then releases itself as an _Object.
 * The stack argument is not read; one result is reported. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_0060826C[], d_00607CB8[], d_008D122C[];
DECOMP_C void __cdecl sub_004030A0(void *L, float n);                  /* lua_pushnumber */
DECOMP_C unsigned int __thiscall sub_00422000(void *self);             /* _Object::~_Object */

DECOMP(004278F0)
int __thiscall f_004278F0(void *this, void *arg)
{
    void *guard[3];

    guard[0] = d_0060826C;
    guard[1] = 0;
    guard[2] = 0;
    sub_004030A0(*(void **)d_008D122C, *(float *)((char *)this + 0x94));
    guard[0] = d_00607CB8;
    sub_00422000(guard);
    return 1;
}
