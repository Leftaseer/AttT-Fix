/* 0x00568F30: registers the method module's direct Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0EB8[];
DECOMP(00568F30)
unsigned int __cdecl f_00568F30(void) { return lua_callback_register_direct(d_008D0EB8); }
