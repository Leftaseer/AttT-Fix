/* CReadCursorDat: the cursor table of Cursors.dat and its loader (0x4A0910 / 0x4A0870 / 0x4A0990).  The table is
 * the same bucket map the interface records use, and each value is a cursor's texture name and two numbers. */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

/* one cursor record: the texture name and the two numbers of its line */
struct CursorRecord {
    std::string text; /* +00 */
    unsigned x;       /* +1C */
    unsigned y;       /* +20 */
};
static_assert(sizeof(CursorRecord) == 0x24, "CursorRecord is 0x24 bytes");
static_assert(__builtin_offsetof(CursorRecord, x) == 0x1C, "CursorRecord::x");

/* the pair the map stores: the lowercased name and the record */
struct CursorRecordPair {
    std::string key;    /* +00 */
    CursorRecord value; /* +1C */
};
static_assert(sizeof(CursorRecordPair) == 0x40, "CursorRecordPair is 0x40 bytes");
static_assert(__builtin_offsetof(CursorRecordPair, value) == 0x1C, "CursorRecordPair::value");

/* a node of the cursor map: the library's links and the pair */
struct CursorRecordNode {
    CursorRecordNode *next; /* +00 */
    CursorRecordNode *prev; /* +04 */
    CursorRecordPair pair;  /* +08 */
};
static_assert(sizeof(CursorRecordNode) == 0x48, "CursorRecordNode is 0x48 bytes");
static_assert(__builtin_offsetof(CursorRecordNode, pair) == 0x08, "CursorRecordNode::pair");

/* the cursor map's sentinel and lifetime (its nodes carry the pair above) */
CursorRecordNode *__stdcall CreateCursorNodeSentinel(); /* 0x4A0750 */
FsHashMap *__thiscall InitCursorMap(FsHashMap *map, const unsigned char *allocator, const void *compare); /* 0x4A07F0 */
void __fastcall ClearCursorNodeList(char *mapObject); /* 0x4430D0 the map's tree part (map + 4) */
CursorRecord *__thiscall CursorMapAtIndex(FsHashMap *map, const std::string *key); /* 0x4437E0 */

struct CReadCursorDat {
    void *vftable; /* +00 CSingleton<CReadCursorDat> */
    FsHashMap map; /* +04 the loaded cursors */

    CReadCursorDat();  /* 0x4A0910 */
    ~CReadCursorDat(); /* 0x4A0870 */
    void Load();       /* 0x4A0990 */
};
static_assert(sizeof(CReadCursorDat) == 0x2C, "CReadCursorDat is 0x2C bytes");
static_assert(__builtin_offsetof(CReadCursorDat, map) == 0x04, "CReadCursorDat::map");
