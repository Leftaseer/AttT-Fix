/* The triggers: iTrigger (0x46F840 / 0x46F8C0), LuaTrigger (0x46FAC0 / 0x46F920 / 0x46FA00 / 0x46F9C0), the
 * userdata push (0x46F980) and the deleting destructor (0x46FB70).  The trigger list at 0x6C905C is a world-level
 * object whose vtable slot 1 adds a trigger and slot 4 removes it; its type is not part of the translation. */
#include "game/common.h"
#include "game/engine.h"
#include "game/lua.h"
#include "game/nscript.h"
#include "game/trigger.h"

inline void *operator new(unsigned int, void *p) { return p; }

namespace {

inline void **TriggerListVtable()
{
    return *(void ***)ORIG_VAR(006C905C, void *);
}

inline void TriggerListAdd(iTrigger *trigger)
{
    void *list = ORIG_VAR(006C905C, void *);
    ((void (__thiscall *)(void *, iTrigger *))TriggerListVtable()[1])(list, trigger);
}

inline void TriggerListRemove(iTrigger *trigger)
{
    void *list = ORIG_VAR(006C905C, void *);
    ((void (__thiscall *)(void *, iTrigger *))TriggerListVtable()[4])(list, trigger);
}

inline int PushUserdataValue(unsigned trigger)
{
    *(unsigned *)ORIG_CALL(00403BF0)(g_luaState, 4) = trigger;
    ORIG_CALL(00403390)(g_luaState, kLuaRegistryIndex, ORIG_VAR(006C0F90, int));
    return ORIG_CALL(004036B0)(g_luaState, -2);
}

} // namespace

DECOMP(0046F840)
iTrigger::iTrigger() : CUpdateObject(std::string(), nullptr)
{
    vftable = d_0060CC94;
    TriggerListAdd(this);
}

DECOMP(0046F8C0)
iTrigger::~iTrigger()
{
    vftable = d_0060CC94;
    TriggerListRemove(this);
}

DECOMP(0046FAC0)
LuaTrigger::LuaTrigger(NsTableGet *arguments) : iTrigger()
{
    vftable = d_0060CCC0;
    NsFunction temporary;
    NsValueRef value = { arguments, 1 };
    function = *value.ToFunction(&temporary);
}

DECOMP(0046F920)
LuaTrigger::~LuaTrigger()
{
    vftable = d_0060CCC0;
}

DECOMP(0046FA00)
void LuaTrigger::Update(float)
{
    char read[sizeof(NsTableGet)];
    NsTableGet *results = function.Call((NsTableGet *)read, 1);
    if (results->count > 0) {
        if (ORIG_CALL(00402EA0)(g_luaState, results->base + 1) != 0 && this)
            ((void (__thiscall *)(LuaTrigger *, int))((void **)vftable)[0])(this, 1);
    }
    results->~NsTableGet();
}

DECOMP(0046F9C0)
int LuaTrigger::PushUserdata()
{
    return PushUserdataValue((unsigned)this);
}

DECOMP(0046F980)
void PushTriggerUserdata(unsigned trigger)
{
    PushUserdataValue(trigger);
}

DECOMP(00568300)
int __stdcall LuaTriggerModuleNew(void)
{
    void *memory = operator new(0x50);
    LuaTrigger *trigger = nullptr;
    if (memory) {
        char read[sizeof(NsTableGet)];
        NsTableGet *results = ::new (read) NsTableGet((NsTable *)ORIG_VAR(008D0990, void *),
                                                      ORIG_CALL(00402A60)(g_luaState) - 1, true);
        trigger = ::new (memory) LuaTrigger(results);
        results->~NsTableGet();
    }
    PushTriggerUserdata((unsigned)trigger);
    return 1;
}

DECOMP(0046FB70)
LuaTrigger *__thiscall DeleteLuaTrigger(LuaTrigger *self, unsigned char flags)
{
    self->~LuaTrigger();
    if (flags & 1)
        operator delete(self);
    return self;
}

/* 0x569F10: the module's named functions enter the table on top of the stack.  Every entry is {name; data}:
 * the closure gets the entry as its upvalue, so the data follows the name. */
DECOMP(00569F10)
void FillLuaTriggerFunctions(const void **entries)
{
    for (const void **entry = entries; *entry; entry += 2) {
        ORIG_CALL(00403120)(g_luaState, (const char *)*entry);
        ORIG_CALL(004032A0)(g_luaState, (void *)entry);
        ORIG_CALL(004031F0)(g_luaState, (void *)d_005683E0, 1);
        ORIG_CALL(004034C0)(g_luaState, -3);
    }
}

/* 0x56E7B0: the module's table in the globals (its "new" builds a LuaTrigger), its metatable in the registry,
 * and the named functions of 0x8D105C in the table the scripts call them through. */
DECOMP(0056E7B0)
void RegisterLuaTriggerModule(const char *name)
{
    void *lua = g_luaState;
    ORIG_VAR(008D0990, const void *) = name;
    ORIG_CALL(00403120)(lua, name);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int module = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004030E0)(lua, d_006114AC, 3);                  /* "new" */
    ORIG_CALL(004031F0)(lua, (void *)d_00568300, 0);
    ORIG_CALL(004034C0)(lua, module);
    ORIG_CALL(004034C0)(lua, kLuaGlobalsIndex);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int methods = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004033D0)(lua, 0, 0);
    int functions = ORIG_CALL(00402A60)(lua);
    ORIG_CALL(004030E0)(lua, d_0060CA4C, 6);                  /* "delete" */
    ORIG_CALL(004031F0)(lua, (void *)d_00563150, 0);
    ORIG_CALL(004034C0)(lua, methods);
    ORIG_CALL(004030E0)(lua, d_0068A54C, 10);                 /* "__tostring" */
    ORIG_CALL(004031F0)(lua, (void *)d_005636D0, 0);
    ORIG_CALL(004034C0)(lua, functions);
    ORIG_CALL(004030E0)(lua, d_00689840, 4);                  /* "__eq" */
    ORIG_CALL(004031F0)(lua, (void *)d_00563020, 0);
    ORIG_CALL(004034C0)(lua, functions);
    ORIG_CALL(004030E0)(lua, d_00689850, 4);                  /* "__gc" */
    ORIG_CALL(004031F0)(lua, (void *)d_00562F60, 0);
    ORIG_CALL(004034C0)(lua, functions);
    ORIG_CALL(004030E0)(lua, d_00689864, 7);                  /* "__index" */
    ORIG_CALL(00402BF0)(lua, methods);
    ORIG_CALL(004034C0)(lua, functions);
    ORIG_VAR(006C0F90, int) = ORIG_CALL(00402190)(lua, kLuaRegistryIndex);
    FillLuaTriggerFunctions((const void **)d_008D105C);
    ORIG_CALL(00402A70)(lua, -2);
}
