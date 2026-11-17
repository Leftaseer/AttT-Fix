/* 0x00567A20: registers the NPC class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0570[];
DECOMP(00567A20)
unsigned int __cdecl f_00567A20(void) { return lua_callback_register(d_008D0570); }
