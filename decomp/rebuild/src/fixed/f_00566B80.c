/* 0x00566B80: registers the GUI scene's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFF40[];
DECOMP(00566B80)
unsigned int __cdecl f_00566B80(void) { return lua_callback_register(d_008CFF40); }
