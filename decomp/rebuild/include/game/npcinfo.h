/* CReadNPCInfo: the NPC table of the global "NPC" Lua table.  Every value of the table becomes one 0x1EC-byte
 * record keyed by its name (0x4A7CE0 / 0x4A7EC0 / 0x4A7BF0 / 0x4A7CC0); the loader 0x4A82F0 walks the table and
 * fills the map at +04, the same 0x28-byte file system bucket map the other loaders use. */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

/* an engine script object (see game/lua.h) */
struct LuaObject;

/* the engine vector storage: an empty allocator and the three pointers (0x2C-byte elements, see NpcAction) */
struct NpcVector {
    unsigned char allocator[4]; /* +00 */
    void *begin;                /* +04 */
    void *end;                  /* +08 */
    void *limit;                /* +0C */
};
static_assert(sizeof(NpcVector) == 0x10, "NpcVector is 0x10 bytes");

/* one entry of the record's "Action", "Talk" and "MoveWorld" tables: the entry key and the four numbers of the
 * entry's table, truncated from the Lua values (the defaults are 2 / 3 / 4 / 5). */
struct NpcAction {
    std::string name; /* +00 */
    int a;            /* +1C */
    int b;            /* +20 */
    int c;            /* +24 */
    int d;            /* +28 */
};
static_assert(sizeof(NpcAction) == 0x2C, "NpcAction is 0x2C bytes");
static_assert(__builtin_offsetof(NpcAction, a) == 0x1C, "NpcAction::a");
static_assert(__builtin_offsetof(NpcAction, d) == 0x28, "NpcAction::d");

/* one value of the "NPC" table: the key, the "ViewDistance" field, the "Action" table and its "Talk" and
 * "MoveWorld" sub-tables, the frame -> action map the Action counts fill, and the value table itself. */
struct NpcInfo {
    std::string name;      /* +000 the key inside the "NPC" table */
    float viewDistance;    /* +01C the "ViewDistance" field */
    NpcVector actions;     /* +020 the "Action" table's entries */
    int frameActions[100]; /* +030 each animation frame's action index */
    NpcVector talks;       /* +1C0 the "Talk" entries */
    NpcVector moves;       /* +1D0 the "MoveWorld" entries */
    LuaObject *value;      /* +1E0 the value table */
    LuaObject *animation;  /* +1E4 unused by the loader */
    LuaObject *unknown;    /* +1E8 unused by the loader */

    NpcInfo();  /* 0x4A7CE0 */
    ~NpcInfo(); /* 0x4A7BF0 */
    void Read(); /* 0x4A7EC0: fills the record from its value table */
};
static_assert(sizeof(NpcInfo) == 0x1EC, "NpcInfo is 0x1EC bytes");
static_assert(__builtin_offsetof(NpcInfo, viewDistance) == 0x01C, "NpcInfo::viewDistance");
static_assert(__builtin_offsetof(NpcInfo, actions) == 0x020, "NpcInfo::actions");
static_assert(__builtin_offsetof(NpcInfo, frameActions) == 0x030, "NpcInfo::frameActions");
static_assert(__builtin_offsetof(NpcInfo, talks) == 0x1C0, "NpcInfo::talks");
static_assert(__builtin_offsetof(NpcInfo, moves) == 0x1D0, "NpcInfo::moves");
static_assert(__builtin_offsetof(NpcInfo, value) == 0x1E0, "NpcInfo::value");

/* the deleting destructor behind the record vtable slot 0 */
NpcInfo *__thiscall DeleteNpcInfo(NpcInfo *info, unsigned char flags); /* 0x4A7CC0 */

/* fills one action from the iterator's current key and four numbers of the current value.  The original takes
 * the action in ECX, ignores EBX (the callers keep one of the record's vectors there across the call) and pops
 * a pointer to the caller's iterator slot from the stack. */
void __cdecl BuildNpcAction(NpcAction *action, unsigned ebx, LuaObject **iterator); /* 0x4A0490 */

struct CReadNPCInfo {
    void *vftable;  /* +00 CSingleton<CReadNPCInfo> */
    FsHashMap npcs; /* +04 the loaded records by name */

    void Load(); /* 0x4A82F0 */
};
static_assert(sizeof(CReadNPCInfo) == 0x2C, "CReadNPCInfo is 0x2C bytes");
static_assert(__builtin_offsetof(CReadNPCInfo, npcs) == 0x04, "CReadNPCInfo::npcs");
