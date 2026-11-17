/* 0x005688C0: registers the editor army's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0BA0[];
DECOMP(005688C0)
unsigned int __cdecl f_005688C0(void) { return lua_callback_register(d_008D0BA0); }
