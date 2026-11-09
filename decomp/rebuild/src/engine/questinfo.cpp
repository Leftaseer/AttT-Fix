/* CReadQuestInfo: the quest table of the "quests" Lua chunk - the loader (0x4A8880) and the 0x24-byte entry
 * (0x4A8620 / 0x4A8780 / 0x4A86E0 / 0x4A8760).  The loader runs the chunk, walks the "Quest" table and keeps
 * one entry per table value: the entry's key, the value table and the table's "CheckFinish" field.  The engine's
 * Lua objects (CLO*) are refcounted at +4; the map at CReadQuestInfo+4 is the file system's bucket map. */
#include "game/common.h"
#include "game/questinfo.h"
#include "game/lua.h"

ORIG_DATA(006C88D4); /* the script machine (CLuaWrapper*) */
ORIG_DATA(008CF0AC); /* the Lua global table object (CLuaObject*) */

/* 0x561C10: an iterator over the object's table entries (the caller takes the reference, like the original) */
ORIG_THISCALL(00561C10, void *, (void *self));
/* 0x561270: a table object for the iterator's current value */
ORIG_THISCALL(00561270, void *, (void *self, void *iterator));
/* 0x561830: the named field of an object */
ORIG_THISCALL(00561830, void *, (void *self, const std::string *name));
/* 0x5626D0: the named field of a table */
ORIG_THISCALL(005626D0, void *, (void *self, const std::string *name));
/* 0x560100: moves a table iterator to its next entry (and drops it when there is none) */
ORIG_THISCALL(00560100, void, (void *self));
/* 0x5542E0: the bucket map's value slot for the key (the caller stores the value there) */
ORIG_THISCALL(005542E0, void **, (FsHashMap *map, const std::string *key));

/* The entry remembers the key of the table object and its "CheckFinish" field.  The references are taken
 * before the old ones are dropped, so a repeated Read of the same table stays valid. */
DECOMP(004A8620)
void QuestEntry::Read(LuaObject *table)
{
    RetainLuaObject(table);
    ReleaseLuaObject(this->table);
    this->table = table;
    name = *(const std::string *)((const char *)table + 0x10);

    std::string fieldName("CheckFinish");
    LuaObject *check = (LuaObject *)sub_005626D0(table, &fieldName);
    RetainLuaObject(check);
    ReleaseLuaObject(checkFinish);
    checkFinish = check;
}

DECOMP(004A8780)
QuestEntry::QuestEntry(LuaObject *value) : name(), table(nullptr), checkFinish(nullptr)
{
    Read(value);
}

DECOMP(004A86E0)
QuestEntry::~QuestEntry()
{
    ReleaseLuaObject(checkFinish);
    ReleaseLuaObject(table);
}

DECOMP(004A8760)
QuestEntry *__thiscall DeleteQuestEntry(QuestEntry *entry, unsigned char flags)
{
    entry->~QuestEntry();
    if (flags & 1)
        operator delete(entry);
    return entry;
}

/* Runs "quests", then walks the "Quest" table.  Every value of the table becomes a table object (0x38 bytes),
 * whose entry is inserted under the key the iterator reports; the loop ends when the iterator has no table
 * value left. */
DECOMP(004A8880)
void CReadQuestInfo::Load()
{
    CLuaWrapper *lua = *(CLuaWrapper **)d_006C88D4;
    lua->DoFile("quests");

    LuaObject *root = *(LuaObject **)d_008CF0AC;
    std::string tableName("Quest");
    LuaObject *table = (LuaObject *)sub_00561830(root, &tableName);
    RetainLuaObject(table);

    LuaObject *iterator = nullptr;
    if (table) {
        iterator = (LuaObject *)sub_00561C10(table);
        RetainLuaObject(iterator);
    }
    if (iterator) {
        do {
            LuaObject *value = (LuaObject *)operator new(0x38);
            sub_00561270(value, iterator);
            QuestEntry *entry = new QuestEntry(value);
            *(QuestEntry **)sub_005542E0(&quests, &iterator->key) = entry;
            sub_00560100(iterator);
        } while (iterator->type == kLuaTable);
        ReleaseLuaObject(iterator);
    }
    ReleaseLuaObject(table);
}
