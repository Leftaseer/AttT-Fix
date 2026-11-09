/* CReadArmyInfo: the "Army" table of the global Lua chunk - the loader (0x492EC0), the 0x2C-byte army record and
 * its troops (0x491A90 ... 0x492210), the pair/node the map stores (0x491FB0 ... 0x492090), the map's own helpers
 * (0x4924B0 / 0x4925A0 / 0x492950 / 0x4929D0 / 0x492D70) and the singleton's lifetime (0x492CD0 / 0x492E40 /
 * 0x492EA0).
 *
 * The engine's Lua objects are refcounted at +04 (game/lua.h).  The map at CReadArmyInfo+4 is the file system's
 * bucket map, so its hash, find and growth are FsHashMap's; the vector algorithms over ArmyTroop are the
 * engine's own instantiations and stay the original functions.  The records are built in raw storage, as the
 * original does, so every builder below is called on unconstructed memory. */
#include "game/common.h"
#include "game/armyinfo.h"
#include "game/fsarchive.h"

ORIG_DATA(0060B914); /* ST_CFG_POS::vftable: the tag every army record carries */
ORIG_DATA(0060FF4C); /* CReadArmyInfo::vftable */
ORIG_DATA(0060FF2C); /* CSingleton<CReadArmyInfo>::vftable */
ORIG_DATA(006C88D4); /* the script machine, CLuaWrapper* */

/* the nScript wrappers the loader and Read use */
ORIG_STDCALL(005608F0, void *, (void));                                    /* the Lua global table object */
ORIG_THISCALL(00561830, void *, (void *self, const std::string *name));    /* the named field */
ORIG_THISCALL(00561520, std::string *, (void *self, std::string *out,
                                        const std::string *name));         /* the named field as a string */
ORIG_THISCALL(005613A0, float, (void *self, const std::string *name));     /* the named field as a number */
ORIG_THISCALL(00561C10, void *, (void *self));                             /* an iterator over a table */
ORIG_THISCALL(00561270, void *, (void *self, void *iterator));             /* the iterator's current table */
ORIG_THISCALL(00560100, void, (void *self));                               /* advance the iterator */

/* the engine's vector<ArmyTroop> instantiations */
ORIG_FN(0048B470, void *, (unsigned count));                                /* the allocator */
ORIG_FN(00495D30, ArmyTroop *, (const ArmyTroop *first, const ArmyTroop *last, ArmyTroop *dst));
ORIG_FN(00496730, ArmyTroop *, (ArmyTroop *dst, unsigned count, const ArmyTroop *value));
ORIG_THISCALL(004999C0, void, (ArmyTroopVector *self, ArmyTroop *position, unsigned count,
                               const ArmyTroop *value));
ORIG_THISCALL(0049A260, void, (ArmyTroopVector *self, const ArmyTroopVector *source));

/* the map's own sentinel and size guard */
ORIG_STDCALL(0047D3F0, ArmyNode *, (void));
ORIG_THISCALL(0047D350, void, (void *mapObject, unsigned count));

inline void *operator new(unsigned int, void *p) { return p; }

/* The "troops" entry: the "creature" field copied into the troop's name and the "qn" field truncated into its
 * number.  The original builds the field names in two short-lived stack strings. */
DECOMP(00491A90)
void __thiscall BuildArmyTroop(ArmyTroop *troop, LuaObject **value)
{
    {
        std::string field("creature");
        std::string text;
        sub_00561520(*value, &text, &field);
        troop->creature = text;
    }
    {
        std::string field("qn");
        troop->qn = (int)(long long)sub_005613A0(*value, &field);
    }
}

/* The troop constructor: an empty name, then the fields of the iterator's value. */
DECOMP(00491BF0)
ArmyTroop *__thiscall InitArmyTroop(ArmyTroop *troop, LuaObject **value)
{
    ::new (&troop->creature) std::string();
    BuildArmyTroop(troop, value);
    return troop;
}

/* Destroys the troops and frees the buffer; the allocator byte stays. */
static void DestroyTroops(ArmyTroopVector *vector)
{
    if (vector->begin) {
        for (ArmyTroop *troop = vector->begin; troop != vector->end; ++troop)
            troop->creature.~basic_string();
        operator delete(vector->begin);
    }
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
}

DECOMP(00491CF0)
void __cdecl DestroyArmyTroops(ArmyTroopVector *vector, void *unusedEax)
{
    (void)unusedEax;
    DestroyTroops(vector);
}

/* The vector copy constructor allocates exactly as many elements as the source holds (the library's range copy
 * needs the length for its size guard) and copies them into the fresh buffer. */
DECOMP(00491D80)
ArmyTroopVector *__thiscall CopyArmyTroopVector(ArmyTroopVector *self, const ArmyTroopVector *other)
{
    unsigned count = other->begin ? (unsigned)(other->end - other->begin) : 0;
    self->begin = nullptr;
    self->end = nullptr;
    self->limit = nullptr;
    if (count == 0)
        return self;
    if (count > 0x7FFFFFFu)
        ThrowVectorLengthError();
    ArmyTroop *first = (ArmyTroop *)sub_0048B470(count);
    self->begin = first;
    self->end = first;
    self->limit = first + count;
    self->end = sub_00495D30(other->begin, other->end, first);
    return self;
}

/* The map's default record: only the tag and the object slots are set.  The position, the flag and the int are
 * left as the caller's storage had them (operator[] then copies that storage into the map). */
DECOMP(00491F30)
ArmyInfo *__thiscall InitArmyInfo(ArmyInfo *self)
{
    self->vftable = d_0060B914;
    self->troops.begin = nullptr;
    self->troops.end = nullptr;
    self->troops.limit = nullptr;
    self->value = nullptr;
    return self;
}

DECOMP(00491EE0)
ArmyInfo *__thiscall CopyArmyInfo(ArmyInfo *self, const ArmyInfo *other)
{
    self->vftable = d_0060B914;
    self->x = other->x;
    self->y = other->y;
    self->z = other->z;
    self->flag = other->flag;
    self->field14 = other->field14;
    CopyArmyTroopVector(&self->troops, &other->troops);
    RetainLuaObject(other->value);
    self->value = other->value;
    return self;
}

DECOMP(00491F50)
void __thiscall DestroyArmyInfo(ArmyInfo *self)
{
    ReleaseLuaObject(self->value);
    DestroyTroops(&self->troops);
}

/* The pair's original destroys the army (its value reference and the troop buffer) first, the key string last. */
DECOMP(00491FB0)
void __thiscall DestroyArmyPair(ArmyPair *self)
{
    DestroyArmyInfo(&self->value);
    self->key.~basic_string();
}

DECOMP(00492000)
ArmyPair *__thiscall BuildArmyPair(ArmyPair *self, const std::string *key, const ArmyInfo *value)
{
    ::new (&self->key) std::string(*key);
    self->value.vftable = d_0060B914;
    self->value.x = value->x;
    self->value.y = value->y;
    self->value.z = value->z;
    self->value.flag = value->flag;
    self->value.field14 = value->field14;
    CopyArmyTroopVector(&self->value.troops, &value->troops);
    RetainLuaObject(value->value);
    self->value.value = value->value;
    return self;
}

DECOMP(00492090)
ArmyPair *__thiscall CopyArmyPair(ArmyPair *self, const ArmyPair *other)
{
    ::new (&self->key) std::string(other->key);
    self->value.vftable = d_0060B914;
    self->value.x = other->value.x;
    self->value.y = other->value.y;
    self->value.z = other->value.z;
    self->value.flag = other->value.flag;
    self->value.field14 = other->value.field14;
    CopyArmyTroopVector(&self->value.troops, &other->value.troops);
    RetainLuaObject(other->value.value);
    self->value.value = other->value.value;
    return self;
}

/* Assignment keeps the tag, copies the five value fields and assigns the troops; the new value is retained
 * before the old one is dropped, so assigning a record to itself stays valid. */
DECOMP(00492130)
ArmyInfo *__thiscall AssignArmyInfo(ArmyInfo *self, const ArmyInfo *other)
{
    self->x = other->x;
    self->y = other->y;
    self->z = other->z;
    self->flag = other->flag;
    self->field14 = other->field14;
    sub_0049A260(&self->troops, &other->troops);
    RetainLuaObject(other->value);
    ReleaseLuaObject(self->value);
    self->value = other->value;
    return self;
}

/* Read walks the "troops" table: every value becomes a table object whose "creature"/"qn" fields fill one troop.
 * The source table is kept before the previous one is dropped.  Like the original, the first entry is taken
 * before the iterator is tested; an element goes into the free slot when there is one and through the vector's
 * insert otherwise. */
DECOMP(00492210)
void __thiscall ReadArmyInfo(ArmyInfo *self, LuaObject *table)
{
    RetainLuaObject(table);
    ReleaseLuaObject(self->value);
    self->value = table;

    std::string key("troops");
    LuaObject *troopsTable = (LuaObject *)sub_00561830(table, &key);
    RetainLuaObject(troopsTable);

    LuaObject *iterator = (LuaObject *)sub_00561C10(troopsTable);
    RetainLuaObject(iterator);

    do {
        LuaObject *object = (LuaObject *)operator new(0x38);
        LuaObject *item = object ? (LuaObject *)sub_00561270(object, iterator) : nullptr;
        RetainLuaObject(item);
        {
            ArmyTroop troop;
            BuildArmyTroop(&troop, &item);
            if (self->troops.begin == nullptr ||
                (unsigned)(self->troops.limit - self->troops.begin) <=
                    (unsigned)(self->troops.end - self->troops.begin))
                sub_004999C0(&self->troops, self->troops.end, 1, &troop);
            else {
                sub_00496730(self->troops.end, 1, &troop);
                ++self->troops.end;
            }
        }
        ReleaseLuaObject(item);
        sub_00560100(iterator);
    } while (iterator->type == kLuaTable);

    ReleaseLuaObject(iterator);
    ReleaseLuaObject(troopsTable);
}

DECOMP(00492450)
ArmyInfo *__thiscall InitArmyInfoFromTable(ArmyInfo *self, LuaObject *table)
{
    self->vftable = d_0060B914;
    self->troops.begin = nullptr;
    self->troops.end = nullptr;
    self->troops.limit = nullptr;
    self->value = nullptr;
    ReadArmyInfo(self, table);
    return self;
}

DECOMP(004924B0)
ArmyNode *__stdcall CreateArmyNode(ArmyNode *next, ArmyNode *prev, const ArmyPair *pair)
{
    ArmyNode *node = (ArmyNode *)operator new(sizeof(ArmyNode));
    node->next = next;
    node->prev = prev;
    CopyArmyPair(&node->pair, pair);
    return node;
}

/* Empties the map's node list (the library's view address is map + 4): every node drops its value reference,
 * frees its troop buffer, destroys the key and is freed. */
DECOMP(004925A0)
void __fastcall ClearArmyMapList(char *mapObject)
{
    ArmyNode *head = *(ArmyNode **)(mapObject + 4);
    ArmyNode *node = head->next;
    head->next = head;
    head->prev = head;
    *(unsigned *)(mapObject + 8) = 0;
    while (node != head) {
        ArmyNode *next = node->next;
        ReleaseLuaObject(node->pair.value.value);
        DestroyTroops(&node->pair.value.troops);
        node->pair.key.~basic_string();
        operator delete(node);
        node = next;
    }
}

DECOMP(00492950)
FsHashMap *__thiscall InitArmyMap(FsHashMap *map, const unsigned char *allocator, const void *compare)
{
    (void)compare;
    *(unsigned char *)map = *allocator;
    map->sentinel = sub_0047D3F0();
    map->size = 0;
    void *sentinel = map->sentinel;
    InitPointerVector(&map->vectorAlloc, 9, &sentinel);
    map->mask = 1;
    map->count = 1;
    return map;
}

/* Inserts a pair into the map: the key is hashed and looked up in its bucket (the nodes are ordered by the
 * case-sensitive std::string operator<); a missing key is linked before its lower bound and the size grows, and
 * the bucket starts that pointed at the lower bound point at the new node instead. */
DECOMP(004929D0)
FsInsertResult *__thiscall InsertArmyNode(FsHashMap *map, FsInsertResult *result, const ArmyPair *entry)
{
    if (map->count <= map->size >> 2)
        map->GrowBuckets(true);

    unsigned bucket = FsHashMap::HashName(&entry->key) & map->mask;
    if (map->count <= bucket)
        bucket += -1 - (map->mask >> 1);
    ArmyNode **buckets = (ArmyNode **)map->begin;
    ArmyNode *position = buckets[bucket + 1];
    if (position != buckets[bucket]) {
        do {
            position = position->prev;
            if (!(entry->key < position->pair.key)) {
                if (!(position->pair.key < entry->key)) {
                    result->node = position;
                    result->inserted = 0;
                    return result;
                }
                position = position->next;
                break;
            }
        } while (position != buckets[bucket]);
    }

    ArmyNode *node = CreateArmyNode(position, position->prev, entry);
    sub_0047D350((char *)map + 4, 1);
    position->prev = node;
    node->prev->next = node;

    ArmyNode *oldFirst = buckets[bucket];
    while (position == oldFirst && (buckets[bucket] = node, bucket != 0)) {
        bucket--;
        oldFirst = buckets[bucket];
    }
    result->node = node;
    result->inserted = 1;
    return result;
}

/* The map's operator[]: the army of the key, or a new node holding the default record.  The default record is
 * copied into a pair, the pair into the node, and the temporaries are destroyed.  The deleted source initialises
 * only the tag and the object slots; the five value fields it copies carry the caller's stack, so they are
 * cleared here (the original read the harness's zero-filled stack). */
DECOMP(00492D70)
ArmyInfo *__thiscall ArmyMapAtIndex(FsHashMap *map, const std::string *key)
{
    ArmyNode *node;
    map->FindName((FsStringNode **)&node, key);
    if (node == (ArmyNode *)map->sentinel) {
        alignas(ArmyInfo) unsigned char recordStorage[sizeof(ArmyInfo)] = {};
        ArmyInfo *record = (ArmyInfo *)recordStorage;
        InitArmyInfo(record);
        alignas(ArmyPair) unsigned char pairStorage[sizeof(ArmyPair)];
        ArmyPair *pair = (ArmyPair *)pairStorage;
        BuildArmyPair(pair, key, record);
        FsInsertResult result;
        InsertArmyNode(map, &result, pair);
        node = (ArmyNode *)result.node;
        DestroyArmyPair(pair);
        DestroyArmyInfo(record);
    }
    return &node->pair.value;
}

/* the original hands the map ctor an uninitialised stack byte for the empty allocator; nothing reads it */
DECOMP(00492E40)
CReadArmyInfo::CReadArmyInfo()
{
    unsigned char allocator = 0;
    vftable = d_0060FF4C;
    InitArmyMap(&armies, &allocator, &allocator);
}

DECOMP(00492CD0)
CReadArmyInfo::~CReadArmyInfo()
{
    vftable = d_0060FF4C;

    if (armies.begin)
        operator delete(armies.begin);
    armies.begin = nullptr;
    armies.end = nullptr;
    armies.limit = nullptr;

    /* the tree part at armies+4 destroys the pairs and frees the nodes */
    ClearArmyMapList((char *)&armies + 4);
    if (armies.sentinel)
        operator delete(armies.sentinel);
    armies.sentinel = nullptr;

    vftable = d_0060FF2C;
}

DECOMP(00492EA0)
CReadArmyInfo *__thiscall DeleteReadArmyInfo(CReadArmyInfo *self, unsigned char flags)
{
    self->~CReadArmyInfo();
    if (flags & 1)
        operator delete(self);
    return self;
}

/* Runs "armys" and walks the global "Army" table.  Every value becomes a table object and an army record; the
 * record is read, then its five value fields and the troops are assigned into the map slot.  The slot's value
 * reference is taken from the record before the record's own reference is dropped. */
DECOMP(00492EC0)
void CReadArmyInfo::Load()
{
    CLuaWrapper *lua = *(CLuaWrapper **)d_006C88D4;
    lua->DoFile("armys");

    LuaObject *root = (LuaObject *)sub_005608F0();
    std::string tableName("Army");
    LuaObject *table = (LuaObject *)sub_00561830(root, &tableName);
    RetainLuaObject(table);

    LuaObject *iterator = (LuaObject *)sub_00561C10(table);
    RetainLuaObject(iterator);

    do {
        LuaObject *object = (LuaObject *)operator new(0x38);
        LuaObject *item = object ? (LuaObject *)sub_00561270(object, iterator) : nullptr;

        /* the original builds the record's tag and object slots in its frame; the five value fields stay as the
         * caller's stack had them (the harness's stack is zero), so the storage is cleared first */
        alignas(ArmyInfo) unsigned char recordStorage[sizeof(ArmyInfo)] = {};
        ArmyInfo *record = (ArmyInfo *)recordStorage;
        InitArmyInfo(record);
        ReadArmyInfo(record, item);

        ArmyInfo *slot = ArmyMapAtIndex(&armies, &iterator->key);
        slot->x = record->x;
        slot->y = record->y;
        slot->z = record->z;
        slot->flag = record->flag;
        slot->field14 = record->field14;
        sub_0049A260(&slot->troops, &record->troops);
        RetainLuaObject(record->value);
        ReleaseLuaObject(slot->value);
        slot->value = record->value;
        DestroyArmyInfo(record);

        sub_00560100(iterator);
    } while (iterator->type == kLuaTable);

    ReleaseLuaObject(iterator);
    ReleaseLuaObject(table);
}
