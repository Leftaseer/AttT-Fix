/* 0x00569280: registers the enemy army's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0FC0[];
DECOMP(00569280)
unsigned int __cdecl f_00569280(void) { return lua_callback_register(d_008D0FC0); }
