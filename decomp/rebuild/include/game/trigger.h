/* The map triggers.  iTrigger (0x38 bytes, vtable 0x60CC94) is the CUpdateObject-based trigger base: its
 * constructor registers the trigger with the game's trigger list (0x6C905C, slot 1 adds, slot 4 removes), its
 * destructor unregisters it.  LuaTrigger (0x50 bytes, vtable 0x60CCC0) runs a Lua function: slot 1 is Update
 * (0x46FA00), slot 10 pushes the trigger as userdata for the script (0x46F9C0).  When the script returns true the
 * trigger deletes itself through its own slot 0 (0x46FB70). */
#pragma once
#include "game/common.h"
#include "game/engine.h"
#include "game/nscript.h"

ORIG_DATA(0060CC94); /* iTrigger::vftable */
ORIG_DATA(0060CCC0); /* LuaTrigger::vftable */
ORIG_DATA(006C0F90); /* metatable of the trigger userdata */
ORIG_DATA(006C905C); /* the trigger list (set by 0x53A6A0) */
ORIG_DATA(008D0990); /* the trigger module's table: its "new" field is 0x568300 */
ORIG_DATA(00562F60); /* the module's "__gc" */
ORIG_DATA(00563020); /* the module's "__eq" */
ORIG_DATA(00563150); /* the module's "delete" */
ORIG_DATA(005636D0); /* the module's "__tostring" */
ORIG_DATA(00568300); /* the module's "new" (translated: LuaTriggerModuleNew) */
ORIG_DATA(005683E0); /* the shared closure of the module's named functions */
ORIG_DATA(008D105C); /* the module's named functions: {name; the closure's data} pairs, 8 bytes each */

ORIG_FN(00403BF0, void *, (void *lua, unsigned int size)); /* lua_newuserdata */
ORIG_FN(004036B0, int, (void *lua, int index));            /* lua_setmetatable */
ORIG_FN(00402EA0, int, (void *lua, int index));            /* lua_toboolean */

struct iTrigger : CUpdateObject {
    iTrigger();   /* 0x46F840: registers with the trigger list */
    ~iTrigger();  /* 0x46F8C0: unregisters */
};
static_assert(sizeof(iTrigger) == 0x38, "iTrigger is 0x38 bytes");

struct LuaTrigger : iTrigger {
    NsFunction function; /* +38 the script the trigger runs */

    explicit LuaTrigger(NsTableGet *arguments); /* 0x46FAC0 */
    ~LuaTrigger();                              /* 0x46F920 */
    void Update(float dt);                      /* 0x46FA00 slot 1 (dt unused) */
    int PushUserdata();                         /* 0x46F9C0 slot 10 */
};
static_assert(sizeof(LuaTrigger) == 0x50, "LuaTrigger is 0x50 bytes");
static_assert(__builtin_offsetof(LuaTrigger, function) == 0x38, "LuaTrigger::function");

void PushTriggerUserdata(unsigned trigger); /* 0x46F980 */

/* the module the scripts see: its table, its metatable ("new", "delete", "__tostring", "__eq", "__gc",
 * "__index") and the named functions 0x8D105C lists */
void RegisterLuaTriggerModule(const char *name);    /* 0x56E7B0 */
void FillLuaTriggerFunctions(const void **entries); /* 0x569F10 */
