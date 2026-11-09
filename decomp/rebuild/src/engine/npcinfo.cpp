/* CReadNPCInfo: the records of the global "NPC" Lua table - the loader (0x4A82F0), the 0x1EC-byte record
 * (0x4A7CE0 / 0x4A7EC0 / 0x4A7BF0 / 0x4A7CC0) and the action element builder (0x4A0490).  The loader walks the
 * table and keeps one record per value; Read follows the value's "Animation" -> "Action" -> "Talk" ->
 * "MoveWorld" chain and fills the action vectors and the frame -> action array.  The engine's Lua objects are
 * refcounted at +4 (game/lua.h); the map at CReadNPCInfo+4 is the file system's bucket map. */
#include "game/common.h"
#include "game/npcinfo.h"
#include "game/lua.h"

/* 0x5608F0: the Lua global table object */
ORIG_FN(005608F0, void *, (void));
/* 0x561830: the named field of an object */
ORIG_THISCALL(00561830, void *, (void *self, const std::string *name));
/* 0x5613A0: the named field as a number */
ORIG_THISCALL(005613A0, float, (void *self, const std::string *name));
/* 0x55F560: the current value as a string (the fallback is its default) */
ORIG_THISCALL(0055F560, void *, (void *self, std::string *out, float fallback));
/* 0x55F4A0: the current value as a number (the argument is its default) */
ORIG_THISCALL(0055F4A0, float, (void *self, float fallback));
/* 0x561C10: an iterator over the object's table entries (the caller takes the reference) */
ORIG_THISCALL(00561C10, void *, (void *self));
/* 0x560100: moves a table iterator to its next entry */
ORIG_THISCALL(00560100, void, (void *self));
/* 0x561270: a table object for the iterator's current value */
ORIG_THISCALL(00561270, void *, (void *self, void *iterator));
/* 0x4A7E30: appends one action to the record's vector */
ORIG_THISCALL(004A7E30, void, (NpcVector *vector, const NpcAction *action));
/* 0x497C10: destroys an action vector (the elements' strings, then the buffer) */
ORIG_FASTCALL(00497C10, void, (NpcVector *vector));
/* 0x5542E0: the bucket map's value slot for the key (the caller stores the value there) */
ORIG_THISCALL(005542E0, void **, (FsHashMap *map, const std::string *key));

DECOMP(004A0490)
void __cdecl BuildNpcAction(NpcAction *action, unsigned ebx, LuaObject **iterator)
{
    (void)ebx;
    LuaObject *object = *iterator;
    std::string text;
    sub_0055F560(object, &text, 1.0f);
    action->name = text;
    action->a = (int)(long long)sub_0055F4A0(object, 2.0f);
    action->b = (int)(long long)sub_0055F4A0(object, 3.0f);
    action->c = (int)(long long)sub_0055F4A0(object, 4.0f);
    action->d = (int)(long long)sub_0055F4A0(object, 5.0f);
}

/* The constructor builds only the name string and the vector/object slots the loader fills; the view distance
 * and the frame array stay uninitialised until Read writes them. */
DECOMP(004A7CE0)
NpcInfo::NpcInfo() : name()
{
    actions.begin = actions.end = actions.limit = nullptr;
    talks.begin = talks.end = talks.limit = nullptr;
    moves.begin = moves.end = moves.limit = nullptr;
    value = nullptr;
    animation = nullptr;
    unknown = nullptr;
}

DECOMP(004A7BF0)
NpcInfo::~NpcInfo()
{
    ReleaseLuaObject(unknown);
    ReleaseLuaObject(animation);
    ReleaseLuaObject(value);
    sub_00497C10(&moves);
    sub_00497C10(&talks);
    sub_00497C10(&actions);
    /* the members' implicit destructors follow: name's string destructor runs last, like the original */
}

DECOMP(004A7CC0)
NpcInfo *__thiscall DeleteNpcInfo(NpcInfo *info, unsigned char flags)
{
    info->~NpcInfo();
    if (flags & 1)
        operator delete(info);
    return info;
}

/* Read takes its references before dropping the old ones; the record's own value table is what everything is
 * read from.  The original creates one action temporary for the whole function, destroys it before the final
 * release, and enters each of the three loops only when its iterator is valid.  Each "Action" entry appends one
 * action and repeats the action's index (`count` frames, default 6, truncated) across the following frame
 * slots; the "Talk" and "MoveWorld" sub-tables append their keys. */
DECOMP(004A7EC0)
void NpcInfo::Read()
{
    LuaObject *table = value;
    RetainLuaObject(table);
    name = *(const std::string *)((const char *)table + 0x10);

    std::string key("ViewDistance");
    viewDistance = sub_005613A0(table, &key);

    key = "Animation";
    LuaObject *animationTable = (LuaObject *)sub_00561830(table, &key);
    RetainLuaObject(animationTable);

    key = "Action";
    LuaObject *actionsTable = (LuaObject *)sub_00561830(animationTable, &key);
    RetainLuaObject(actionsTable);

    LuaObject *talkTable = nullptr;
    LuaObject *talkIterator = nullptr;
    LuaObject *moveTable = nullptr;
    LuaObject *moveIterator = nullptr;
    {
        NpcAction action;
        LuaObject *iterator = (LuaObject *)sub_00561C10(actionsTable);
        RetainLuaObject(iterator);

        int frameAction = 0;
        unsigned frame = 0;
        while (iterator) {
            BuildNpcAction(&action, 0, &iterator);
            sub_004A7E30(&actions, &action);

            unsigned end = frame + (unsigned)(long long)sub_0055F4A0(iterator, 6.0f);
            for (unsigned i = frame; i < end; i++)
                frameActions[i] = frameAction;
            frame = end;
            frameAction++;

            sub_00560100(iterator);
            if (iterator->type != kLuaTable)
                break;
        }

        key = "Talk";
        talkTable = (LuaObject *)sub_00561830(actionsTable, &key);
        RetainLuaObject(talkTable);
        ReleaseLuaObject(actionsTable);

        talkIterator = (LuaObject *)sub_00561C10(talkTable);
        RetainLuaObject(talkIterator);
        ReleaseLuaObject(iterator);

        while (talkIterator) {
            BuildNpcAction(&action, 0, &talkIterator);
            sub_004A7E30(&talks, &action);
            sub_00560100(talkIterator);
            if (talkIterator->type != kLuaTable)
                break;
        }

        key = "MoveWorld";
        moveTable = (LuaObject *)sub_00561830(talkTable, &key);
        RetainLuaObject(moveTable);
        ReleaseLuaObject(talkTable);

        moveIterator = (LuaObject *)sub_00561C10(moveTable);
        RetainLuaObject(moveIterator);
        ReleaseLuaObject(talkIterator);

        while (moveIterator) {
            BuildNpcAction(&action, 0, &moveIterator);
            sub_004A7E30(&moves, &action);
            sub_00560100(moveIterator);
            if (moveIterator->type != kLuaTable)
                break;
        }
    }
    ReleaseLuaObject(moveIterator);
    ReleaseLuaObject(moveTable);
    ReleaseLuaObject(animationTable);
    ReleaseLuaObject(table);
}

/* Load walks the global "NPC" table (the chunk itself is run elsewhere) and keys every value's record by the
 * entry name.  The loop takes its first iteration before the iterator is tested, like the original (the loader
 * only runs when the chunk defined the table); the record and its value object are allocated before their
 * constructors run. */
DECOMP(004A82F0)
void CReadNPCInfo::Load()
{
    LuaObject *root = (LuaObject *)sub_005608F0();
    std::string tableName("NPC");
    LuaObject *table = (LuaObject *)sub_00561830(root, &tableName);
    RetainLuaObject(table);

    LuaObject *iterator = (LuaObject *)sub_00561C10(table);
    RetainLuaObject(iterator);

    do {
        NpcInfo *info = new NpcInfo();
        LuaObject *value = (LuaObject *)operator new(0x38);
        if (value)
            sub_00561270(value, iterator);
        RetainLuaObject(value);
        ReleaseLuaObject(info->value);
        info->value = value;
        info->Read();
        *(NpcInfo **)sub_005542E0(&npcs, &iterator->key) = info;
        sub_00560100(iterator);
    } while (iterator->type == kLuaTable);
    ReleaseLuaObject(iterator);
    ReleaseLuaObject(table);
}
