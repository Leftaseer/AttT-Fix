/* The triggers: iTrigger (0x46F840 / 0x46F8C0), LuaTrigger (0x46FAC0 / 0x46F920 / 0x46FA00 / 0x46F9C0), the
 * userdata push (0x46F980) and the deleting destructor (0x46FB70).  The trigger list at 0x6C905C is a world-level
 * object whose vtable slot 1 adds a trigger and slot 4 removes it; its type is not part of the translation. */
#include "game/common.h"
#include "game/engine.h"
#include "game/lua.h"
#include "game/nscript.h"
#include "game/trigger.h"

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

DECOMP(0046FB70)
LuaTrigger *__thiscall DeleteLuaTrigger(LuaTrigger *self, unsigned char flags)
{
    self->~LuaTrigger();
    if (flags & 1)
        operator delete(self);
    return self;
}
