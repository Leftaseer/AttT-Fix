/* CReadArmyInfo: the army table of the global "Army" Lua table (loader 0x492EC0).  Every value of the table
 * becomes one ArmyInfo record keyed by the entry name in the same bucket map the other loaders use; a record is
 * a position (x/y/z), a flag, an int and a vector of troops, each troop a "creature" name and a "qn" count.
 *
 * The records are plain layouts the original builds in place (stack storage or a raw operator new block), so the
 * builders below are functions rather than constructors: the generated code names each one uniquely and the map,
 * the pair and the loader all drive them explicitly.  The generic vector algorithms the engine instantiates once
 * per element type stay the original functions (declared below). */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"
#include "game/lua.h"

/* one troop of an army: the "creature" name and the "qn" number */
struct ArmyTroop {
    std::string creature; /* +00 */
    int qn;               /* +1C */
};
static_assert(sizeof(ArmyTroop) == 0x20, "ArmyTroop is 0x20 bytes");
static_assert(__builtin_offsetof(ArmyTroop, qn) == 0x1C, "ArmyTroop::qn");

/* vector<ArmyTroop> (0x10 bytes), the engine's usual storage */
struct ArmyTroopVector {
    unsigned char allocator[4]; /* +00 */
    ArmyTroop *begin;           /* +04 */
    ArmyTroop *end;             /* +08 */
    ArmyTroop *limit;           /* +0C */
};
static_assert(sizeof(ArmyTroopVector) == 0x10, "ArmyTroopVector is 0x10 bytes");
static_assert(__builtin_offsetof(ArmyTroopVector, begin) == 0x04, "ArmyTroopVector::begin");

/* one army: the ST_CFG_POS tag/vftable at +00, the position, the loader-copied flag and int, the troops and the
 * value table the record was read from */
struct ArmyInfo {
    void *vftable;          /* +00 ST_CFG_POS::vftable */
    float x;                /* +04 */
    float y;                /* +08 */
    float z;                /* +0C */
    unsigned char flag;     /* +10 */
    int field14;            /* +14 */
    ArmyTroopVector troops; /* +18 */
    LuaObject *value;       /* +28 the value table */
};
static_assert(sizeof(ArmyInfo) == 0x2C, "ArmyInfo is 0x2C bytes");
static_assert(__builtin_offsetof(ArmyInfo, flag) == 0x10, "ArmyInfo::flag");
static_assert(__builtin_offsetof(ArmyInfo, field14) == 0x14, "ArmyInfo::field14");
static_assert(__builtin_offsetof(ArmyInfo, troops) == 0x18, "ArmyInfo::troops");
static_assert(__builtin_offsetof(ArmyInfo, value) == 0x28, "ArmyInfo::value");

/* the pair the map stores: the entry name and the army */
struct ArmyPair {
    std::string key; /* +00 */
    ArmyInfo value;  /* +1C */
};
static_assert(sizeof(ArmyPair) == 0x48, "ArmyPair is 0x48 bytes");
static_assert(__builtin_offsetof(ArmyPair, value) == 0x1C, "ArmyPair::value");

/* a node of the army map: the library's links and the pair */
struct ArmyNode {
    ArmyNode *next; /* +00 */
    ArmyNode *prev; /* +04 */
    ArmyPair pair;  /* +08 */
};
static_assert(sizeof(ArmyNode) == 0x50, "ArmyNode is 0x50 bytes");
static_assert(__builtin_offsetof(ArmyNode, pair) == 0x08, "ArmyNode::pair");

/* The engine's vector<ArmyTroop> instantiations stay the original functions, declared with ORIG_FN in the source:
 * the allocator (0x48B470), the range copy (0x495D30), the fill (0x496730), the insert (0x4999C0) and the
 * assignment (0x49A260). */

/* troop and record builders and operations */
void __thiscall BuildArmyTroop(ArmyTroop *troop, LuaObject **value);   /* 0x491A90 */
ArmyTroop *__thiscall InitArmyTroop(ArmyTroop *troop, LuaObject **value); /* 0x491BF0 */
/* 0x491CF0 reads the vector from ECX and leaves a dead EAX input, so the replacement lists both registers */
void __cdecl DestroyArmyTroops(ArmyTroopVector *vector, void *unusedEax);
ArmyTroopVector *__thiscall CopyArmyTroopVector(ArmyTroopVector *self,
                                                const ArmyTroopVector *other); /* 0x491D80 */
ArmyInfo *__thiscall CopyArmyInfo(ArmyInfo *self, const ArmyInfo *other);      /* 0x491EE0 */
ArmyInfo *__thiscall InitArmyInfo(ArmyInfo *self);                            /* 0x491F30 */
void __thiscall DestroyArmyInfo(ArmyInfo *self);                              /* 0x491F50 */
ArmyInfo *__thiscall AssignArmyInfo(ArmyInfo *self, const ArmyInfo *other);   /* 0x492130 */
void __thiscall ReadArmyInfo(ArmyInfo *self, LuaObject *table);               /* 0x492210 */
ArmyInfo *__thiscall InitArmyInfoFromTable(ArmyInfo *self, LuaObject *table); /* 0x492450 */

/* pair builders and the map's helpers */
void __thiscall DestroyArmyPair(ArmyPair *self);                              /* 0x491FB0 */
ArmyPair *__thiscall BuildArmyPair(ArmyPair *self, const std::string *key,
                                   const ArmyInfo *value);                    /* 0x492000 */
ArmyPair *__thiscall CopyArmyPair(ArmyPair *self, const ArmyPair *other);     /* 0x492090 */

/* the army map: its initialiser (map + all the library's empty state), emptyer, node factory, insert and
 * operator[] (the sentinel and the size guard are the original 0x47D3F0 / 0x47D350) */
FsHashMap *__thiscall InitArmyMap(FsHashMap *map, const unsigned char *allocator, const void *compare); /* 0x492950 */
void __fastcall ClearArmyMapList(char *mapObject); /* 0x4925A0 the map's tree part (map + 4) */
ArmyNode *__stdcall CreateArmyNode(ArmyNode *next, ArmyNode *prev, const ArmyPair *pair); /* 0x4924B0 */
FsInsertResult *__thiscall InsertArmyNode(FsHashMap *map, FsInsertResult *result,
                                          const ArmyPair *entry); /* 0x4929D0 */
ArmyInfo *__thiscall ArmyMapAtIndex(FsHashMap *map, const std::string *key); /* 0x492D70 */

struct CReadArmyInfo {
    void *vftable; /* +00 CSingleton<CReadArmyInfo> */
    FsHashMap armies; /* +04 the loaded records by name */

    CReadArmyInfo();  /* 0x492E40 */
    ~CReadArmyInfo(); /* 0x492CD0 */
    void Load();      /* 0x492EC0 */
};
static_assert(sizeof(CReadArmyInfo) == 0x2C, "CReadArmyInfo is 0x2C bytes");
static_assert(__builtin_offsetof(CReadArmyInfo, armies) == 0x04, "CReadArmyInfo::armies");

/* the deleting destructor behind the record vtable slot 0 */
CReadArmyInfo *__thiscall DeleteReadArmyInfo(CReadArmyInfo *self, unsigned char flags); /* 0x492EA0 */
