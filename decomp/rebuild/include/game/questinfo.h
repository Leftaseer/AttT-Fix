/* CReadQuestInfo: the quest table the "quests" Lua chunk defines.  Every entry of the chunk's "Quest" table
 * becomes one QuestEntry in the loader's name map (0x4A8880); the entry keeps the table object and its
 * "CheckFinish" field.  The map is the file system's bucket map, the same one the cursor table uses. */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

/* a script object (the engine's CLO* family): the refcount at +4 and the table/key members the loaders use */
struct LuaObject;

/* one quest of the table: the entry's key, its table and the table's "CheckFinish" */
struct QuestEntry {
    std::string name;         /* +00 the key inside the "Quest" table */
    LuaObject *table;         /* +1C the entry's table object */
    LuaObject *checkFinish;   /* +20 its "CheckFinish" field */

    explicit QuestEntry(LuaObject *table); /* 0x4A8780 */
    void Read(LuaObject *table);           /* 0x4A8620 */
    ~QuestEntry();                         /* 0x4A86E0 */
};
static_assert(sizeof(QuestEntry) == 0x24, "QuestEntry is 0x24 bytes");
static_assert(__builtin_offsetof(QuestEntry, table) == 0x1C, "QuestEntry::table");
static_assert(__builtin_offsetof(QuestEntry, checkFinish) == 0x20, "QuestEntry::checkFinish");

/* the deleting destructor behind the class vtable slot 0 */
QuestEntry *__thiscall DeleteQuestEntry(QuestEntry *entry, unsigned char flags); /* 0x4A8760 */

struct CReadQuestInfo {
    void *vftable;    /* +00 CSingleton<CReadQuestInfo> */
    FsHashMap quests; /* +04 the loaded quests by name */

    void Load();      /* 0x4A8880 */
};
static_assert(sizeof(CReadQuestInfo) == 0x2C, "CReadQuestInfo is 0x2C bytes");
static_assert(__builtin_offsetof(CReadQuestInfo, quests) == 0x04, "CReadQuestInfo::quests");
