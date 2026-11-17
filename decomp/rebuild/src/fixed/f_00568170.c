/* 0x00568170: registers the item icon's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0888[];
DECOMP(00568170)
unsigned int __cdecl f_00568170(void) { return lua_callback_register(d_008D0888); }
