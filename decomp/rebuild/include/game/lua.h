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
ORIG_FN(00402A70, void, (void *lua, int index));              /* lua_settop */
ORIG_FN(00402F40, int, (unsigned ebx, void *lua, int index)); /* lua_objlen */
ORIG_FN(00403390, void, (void *lua, int index, int n));       /* lua_rawgeti */

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
