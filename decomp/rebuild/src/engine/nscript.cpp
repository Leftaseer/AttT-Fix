/* nScript::Function and nScript::TableGet: the script machine's references to Lua values.  A Function keeps a
 * registry reference to a function (and optionally the table it is called with), a call leaves its results as a
 * TableGet over the top of the Lua stack, and the handlers of the Lua globals read single values out of it. */
#include "game/common.h"
#include "game/nscript.h"
#include "game/lua.h"

ORIG_FN(00402BF0, void, (void *L, int index));                /* lua_pushvalue */
ORIG_FN(00402190, int, (void *L, int t));                     /* luaL_ref */
ORIG_FN(00402270, void, (void *L, int t, int ref));           /* luaL_unref */
ORIG_FN(00402A60, int, (void *L));                            /* lua_gettop */
ORIG_FN(00403800, void, (void *L, int nargs, int nresults));  /* lua_call */

inline void *operator new(unsigned int, void *p) { return p; }

DECOMP(0046F790)
NsFunction::NsFunction(int index)
{
    vftable = d_006098F0;
    ORIG_CALL(00402BF0)(g_luaState, index);
    reference = ORIG_CALL(00402190)(g_luaState, kLuaRegistryIndex);
}

/* The destructor drops the registry reference; the members then destroy the table and the Object base. */
DECOMP(004378D0)
NsFunction::~NsFunction()
{
    vftable = d_006098F0;
    if (reference > 0)
        ORIG_CALL(00402270)(g_luaState, kLuaRegistryIndex, reference);
}

DECOMP(00436FD0)
NsFunction &NsFunction::operator=(const NsFunction &other)
{
    if (reference > 0)
        ORIG_CALL(00402270)(g_luaState, kLuaRegistryIndex, reference);
    ORIG_CALL(00403390)(g_luaState, kLuaRegistryIndex, other.reference);
    reference = ORIG_CALL(00402190)(g_luaState, kLuaRegistryIndex);
    table = other.table;
    return *this;
}

DECOMP(0057A180)
NsTableGet *NsFunction::Call(NsTableGet *out, int results)
{
    int before = ORIG_CALL(00402A60)(g_luaState);
    ORIG_CALL(00403390)(g_luaState, kLuaRegistryIndex, reference);
    if (table.reference < 1) {
        ORIG_CALL(00403800)(g_luaState, 0, results);
    } else {
        ORIG_CALL(00403390)(g_luaState, kLuaRegistryIndex, table.reference);
        ORIG_CALL(00403800)(g_luaState, 1, results);
    }
    int count = ORIG_CALL(00402A60)(g_luaState) - before;
    return ::new (out) NsTableGet((NsTable *)d_0061D90C, count, true);
}

DECOMP(004277B0)
NsTableGet::NsTableGet(NsTable *table, int count, bool owns)
    : table(table), count(count), base(ORIG_CALL(00402A60)(g_luaState) - count), owns(owns)
{
    vftable = d_00608260;
}

DECOMP(00427820)
NsTableGet::~NsTableGet()
{
    vftable = d_00608260;
    if (count > 0) {
        if (owns)
            ORIG_CALL(00402A70)(g_luaState, -1 - count);
        count = 0;
    }
}

/* A Function of the value at `position` in the read (the first value is 1). */
DECOMP(0046F810)
NsFunction *NsTableGet::FunctionAt(NsFunction *out, int position) const
{
    ::new (out) NsFunction(base + position);
    return out;
}

DECOMP(0046FA90)
NsFunction *NsValueRef::ToFunction(NsFunction *out) const
{
    return values->FunctionAt(out, position);
}
