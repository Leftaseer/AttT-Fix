/* Lua 5.1 math library functions of the engine (lmathlib.c), rebuilt from source.
 * The engine is built with LUA_NUMBER = float and /LTCG, so luaL_checknumber takes L in EAX. */
#include "decomp.h"

typedef struct lua_State lua_State;
typedef struct { lua_Number n; int tt; } TValue;
#define L_TOP(L) (*(TValue **)((char *)(L) + 8))
#define LUA_TNUMBER 3

ORIG_FN(00401680, lua_Number, (lua_State *L /* EAX */, int narg));   /* luaL_checknumber */
#define luaL_checknumber(L, n) ORIG_CALL(00401680)(L, n)

static void lua_pushnumber(lua_State *L, lua_Number n)
{
    TValue *top = L_TOP(L);
    top->n = n;
    top->tt = LUA_TNUMBER;
    L_TOP(L) = top + 1;
}

DECOMP(004064D0)
int math_abs(lua_State *L)
{
    lua_Number x = luaL_checknumber(L, 1);
    lua_pushnumber(L, __builtin_fabsf(x));
    return 1;
}
