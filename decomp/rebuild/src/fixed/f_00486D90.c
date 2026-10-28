/* Lua_006C6D10::StopAnim 0x00486D90: the Lua method stops the animation (flag at 0x1E4), returns no values */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00486D90)
int __thiscall f_00486D90(void *this, void *args)
{
    *(unsigned char *)((char *)this + 0x1e4) = 0;
    return 0;
}
