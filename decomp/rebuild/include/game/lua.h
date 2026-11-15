/* The script machine (CLuaWrapper, the singleton at 0x6C88D4): the Lua state and the chunks the game runs in it.
 * Only the entry points the translated code calls are declared. */
#pragma once
#include "game/common.h"

struct CLuaWrapper {
    void DoFile(const char *fileName); /* 0x432620: runs fileName with ".lua" appended, loaded from the archive */
};

/* An engine script object (the CLO* family): every value, table and iterator starts with these members.  While a
 * table iterator is valid, +08 is the Lua type of the current value, +0C its registry reference and +10 its key. */
struct LuaObject {
    void *vftable;    /* +00 */
    int refCount;     /* +04 */
    int type;         /* +08 */
    int valueRef;     /* +0C */
    std::string key;  /* +10 */
};

static const int kLuaTable = 5;
static const int kLuaRegistryIndex = -10000;
static const int kLuaGlobalsIndex = -10002;

/* The raw Lua 5.1 API the nScript wrappers and the loaders drive directly (the original's fastcall builds of
 * these read EBX, so lua_objlen names that register first). */
ORIG_DATA(008D122C); /* lua_State* */
#define g_luaState ORIG_VAR(008D122C, void *)
ORIG_FN(00402190, int, (void *lua, int index));                    /* luaL_ref */
ORIG_FN(00402A60, int, (void *lua));                               /* lua_gettop */
ORIG_FN(00402A70, void, (void *lua, int index));                   /* lua_settop */
ORIG_FN(00402BF0, void, (void *lua, int index));                   /* lua_pushvalue */
ORIG_FN(00402F40, int, (unsigned ebx, void *lua, int index));      /* lua_objlen */
ORIG_FN(00403080, void, (void *lua));                              /* lua_pushnil */
ORIG_FN(004030A0, void, (void *lua, float number));                /* lua_pushnumber */
ORIG_FN(004030E0, void, (void *lua, const char *text, unsigned len)); /* lua_pushlstring */
ORIG_FN(00403120, void, (void *lua, const char *text));            /* lua_pushstring */
ORIG_FN(004031F0, void, (void *lua, void *function, int upvalues)); /* lua_pushcclosure */
ORIG_FN(004032A0, void, (void *lua, void *pointer));               /* lua_pushlightuserdata */
ORIG_FN(00403390, void, (void *lua, int index, int n));            /* lua_rawgeti */
ORIG_FN(004033D0, void, (void *lua, int arraySize, int hashSize)); /* lua_createtable */
ORIG_FN(004034C0, void, (void *lua, int index));                   /* lua_settable */
ORIG_FN(00403610, void, (void *lua, int index, int n));            /* lua_rawseti */

/* the module tables' fields (every script module's registrar pushes these) */
ORIG_DATA(0060CA4C); /* "delete" */
ORIG_DATA(006114AC); /* "new" */
ORIG_DATA(00689840); /* "__eq" */
ORIG_DATA(00689850); /* "__gc" */
ORIG_DATA(00689864); /* "__index" */
ORIG_DATA(0068A54C); /* "__tostring" */

inline void RetainLuaObject(LuaObject *object)
{
    if (object)
        ++object->refCount;
}

inline void ReleaseLuaObject(LuaObject *object)
{
    if (object && --object->refCount == 0)
        (*(void (__thiscall **)(LuaObject *, int))object->vftable)(object, 1);
}
