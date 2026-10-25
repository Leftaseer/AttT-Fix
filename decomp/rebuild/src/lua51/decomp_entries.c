/* The game's Lua 5.1.2 (0x401000-0x4205A0) replaced by the sources in this folder, unmodified but for luaconf.h
 * (LUA_NUMBER float).  The rest of the game reaches Lua through these functions only: the API, the auxiliary
 * library, and a few internals the game's own code calls (0x4B44C0 builds function prototypes itself:
 * luaM_realloc_, luaS_newlstr, luaD_growstack, luaF_newproto).  Each declaration below makes the original at
 * that address jump to ours; the original Lua code is then unreachable, its data unused (no mutable data is
 * shared with the game: only string and float constants the linker pooled).  The structures (lua_State,
 * global_State, TValue, Proto) are the standard ones of 5.1.2, which the game's code reads at the same offsets.
 *
 * Built as C++ with exceptions like the original (LUAI_THROW: an error is a C++ exception that unwinds the game's
 * frames between, running their destructors).  Addresses from tools/libmatch.py (out/attt_lua.tsv) and from the
 * order of lapi.c in the binary, each checked against the decompiled original.  DECOMP_STACK: the analysis saw
 * register inputs that only pass through to internals with /LTCG conventions (decomp.h). */
#include "decomp.h"

#define LUA_CORE
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
#include "lmem.h"
#include "lstring.h"
#include "ldo.h"
#include "lfunc.h"
#include "lundump.h"

/* lauxlib.c */
DECOMP(00402190) LUALIB_API int luaL_ref(lua_State *L, int t);
DECOMP(00402270) LUALIB_API void luaL_unref(lua_State *L, int t, int ref);
DECOMP(00402410) LUALIB_API int luaL_loadfile(lua_State *L, const char *filename);
DECOMP(004026F0) LUALIB_API int luaL_loadbuffer(lua_State *L, const char *buff, size_t sz, const char *name);
DECOMP(00402870) LUALIB_API lua_State *luaL_newstate(void);
/* lapi.c */
DECOMP(00402960) LUA_API int lua_checkstack(lua_State *L, int size);
DECOMP(00402A60) LUA_API int lua_gettop(lua_State *L);
DECOMP(00402A70) LUA_API void lua_settop(lua_State *L, int idx);
DECOMP(00402AC0) LUA_API void lua_remove(lua_State *L, int idx);
DECOMP(00402B00) LUA_API void lua_insert(lua_State *L, int idx);
DECOMP(00402BF0) LUA_API void lua_pushvalue(lua_State *L, int idx);
DECOMP(00402C20) LUA_API int lua_type(lua_State *L, int idx);
DECOMP(00402C40) LUA_API const char *lua_typename(lua_State *L, int t);
DECOMP(00402C80) LUA_API int lua_isnumber(lua_State *L, int idx);
DECOMP(00402CC0) LUA_API int lua_isstring(lua_State *L, int idx);
DECOMP(00402D10) LUA_API int lua_rawequal(lua_State *L, int idx1, int idx2);
DECOMP(00402DE0) LUA_API lua_Number lua_tonumber(lua_State *L, int idx);
DECOMP(00402E40) LUA_API lua_Integer lua_tointeger(lua_State *L, int idx);
DECOMP(00402EA0) LUA_API int lua_toboolean(lua_State *L, int idx);
DECOMP_STACK(00402ED0) LUA_API const char *lua_tolstring(lua_State *L, int idx, size_t *len);
DECOMP_STACK(00402F40) LUA_API size_t lua_objlen(lua_State *L, int idx);
DECOMP(00402FD0) LUA_API void *lua_touserdata(lua_State *L, int idx);
DECOMP(00403000) LUA_API lua_State *lua_tothread(lua_State *L, int idx);
DECOMP(00403080) LUA_API void lua_pushnil(lua_State *L);
DECOMP(004030A0) LUA_API void lua_pushnumber(lua_State *L, lua_Number n);
DECOMP(004030E0) LUA_API void lua_pushlstring(lua_State *L, const char *s, size_t len);
DECOMP(00403120) LUA_API void lua_pushstring(lua_State *L, const char *s);
DECOMP(004031F0) LUA_API void lua_pushcclosure(lua_State *L, lua_CFunction fn, int n);
DECOMP(00403280) LUA_API void lua_pushboolean(lua_State *L, int b);
DECOMP(004032A0) LUA_API void lua_pushlightuserdata(lua_State *L, void *p);
DECOMP(00403300) LUA_API void lua_getfield(lua_State *L, int idx, const char *k);
DECOMP(00403360) LUA_API void lua_rawget(lua_State *L, int idx);
DECOMP(00403390) LUA_API void lua_rawgeti(lua_State *L, int idx, int n);
DECOMP(004033D0) LUA_API void lua_createtable(lua_State *L, int narr, int nrec);
DECOMP(004034C0) LUA_API void lua_settable(lua_State *L, int idx);
DECOMP(004034F0) LUA_API void lua_setfield(lua_State *L, int idx, const char *k);
DECOMP(00403560) LUA_API void lua_rawset(lua_State *L, int idx);
DECOMP(00403610) LUA_API void lua_rawseti(lua_State *L, int idx, int n);
DECOMP(004036B0) LUA_API int lua_setmetatable(lua_State *L, int objindex);
DECOMP(00403800) LUA_API void lua_call(lua_State *L, int nargs, int nresults);
DECOMP(00403860) LUA_API int lua_pcall(lua_State *L, int nargs, int nresults, int errfunc);
DECOMP(00403940) LUA_API int lua_cpcall(lua_State *L, lua_CFunction func, void *ud);
DECOMP(00403A00) LUA_API int lua_gc(lua_State *L, int what, int data);
DECOMP(00403B00) LUA_API int lua_next(lua_State *L, int idx);
DECOMP(00403BF0) LUA_API void *lua_newuserdata(lua_State *L, size_t size);
/* internals the game calls */
DECOMP(00403E90) LUAI_FUNC void *luaM_toobig(lua_State *L);
DECOMP(00403EB0) LUAI_FUNC void *luaM_realloc_(lua_State *L, void *block, size_t oldsize, size_t size);
DECOMP(00404090) LUAI_FUNC TString *luaS_newlstr(lua_State *L, const char *str, size_t l);
DECOMP(00404620) LUAI_FUNC void luaD_growstack(lua_State *L, int n);
DECOMP(00405520) LUAI_FUNC Proto *luaF_newproto(lua_State *L);
DECOMP_STACK(00405C80) LUAI_FUNC int luaU_dump(lua_State *L, const Proto *f, lua_Writer w, void *data, int strip);
/* lstate.c, linit.c, lmathlib.c */
DECOMP(004061D0) LUA_API void lua_close(lua_State *L);
DECOMP(00406E60) LUALIB_API int luaopen_math(lua_State *L);
DECOMP(00406F00) LUALIB_API void luaL_openlibs(lua_State *L);
