/* CFileSystem: the pak archive file system (0xB8 bytes, singleton 0x6C8C28).
 *
 * A pak is "GRES" + 12-byte header {magic; version; entry count} followed by 0x88-byte directory records
 * {name[0x80]; offset; size}.  The paks are chained as Resource0.pak, Resource1.pak, ... until one cannot be
 * opened; the file directories of all of them go into one map<string, PakEntry> (a later pak overrides an
 * earlier one).  version 200 paks are XOR-encrypted with the 16-byte key at 0x6C04B4 (the header count and the
 * whole directory block). */
#pragma once
#include "game/common.h"
#include "msvc8/fstream.h"

/* The file system library's own bucket hash map (0x28 bytes): all nodes are also in one doubly linked list
 * through the sentinel at +08; the vector at +10..+1F holds the per-bucket list ends, +20 is the bucket mask
 * and +24 the number of buckets. */
struct FsHashMap {
    unsigned char allocator[8]; /* +00 */
    void *sentinel;             /* +08 */
    unsigned size;              /* +0C */
    void *vectorAlloc;          /* +10 std::allocator, unused */
    void *begin;                /* +14 */
    void *end;                  /* +18 */
    void *limit;                /* +1C */
    unsigned mask;              /* +20 */
    unsigned count;             /* +24 */
};
static_assert(sizeof(FsHashMap) == 0x28, "FsHashMap is 0x28 bytes");

/* a node of a string-keyed map: the key at +08, the value after it at +24 */
struct FsStringNode {
    FsStringNode *next; /* +00 */
    FsStringNode *prev; /* +04 */
    std::string key;    /* +08 */
};
static_assert(__builtin_offsetof(FsStringNode, key) == 0x08, "FsStringNode::key");

/* a node of the int-keyed map of the open pak streams (0x10 bytes) */
struct FsIntNode {
    FsIntNode *next; /* +00 */
    FsIntNode *prev; /* +04 */
    int key;         /* +08 the index in the ResourceN.pak chain */
    void *value;     /* +0C std::ifstream* */
};
static_assert(sizeof(FsIntNode) == 0x10, "FsIntNode is 0x10 bytes");

/* the value of map<string, PakEntry> / the directory record as the map keeps it (0x28 bytes) */
struct PakEntry {
    std::string name; /* +00 the map key */
    unsigned offset;  /* +1C */
    unsigned size;    /* +20 */
    int pak;          /* +24 index of the pak the file is in */
};

/* one 0x88-byte record of a pak directory */
struct PakRecord {
    char name[0x80];
    unsigned offset;
    unsigned size;
};

struct CFileSystem {
    void *vftable;                /* +00 CFileSystem, 0x60B140 in the singleton teardown */
    int pakVersion;               /* +04 200 = the encrypted format */
    unsigned char unused08[4];    /* +08 XORed with the key, never read */
    int pakCount;                 /* +0C entries in the last pak read */
    FsHashMap files;              /* +10 map<string, PakEntry> of all paks */
    FsHashMap streams;            /* +38 map<int, std::ifstream*> of the opened paks */
    std::string archiveName;      /* +60 name of the last pak tried */
    bool paksOpened;              /* +7C */
    unsigned char pad7D[3];
    std::ifstream *currentStream; /* +80 stream of the last pak */
    FsStringNode *lastEntry;      /* +84 node found by the last OpenFile */
    unsigned char embedded[0x30]; /* +88 file system object, built by 0x577C60: a std::string at +0 (destroyed
                                   * by hand in ~CFileSystem) and a tree map {pad, sentinel +4, size +8} at +1C */

    CFileSystem();                           /* 0x451E00 */
    ~CFileSystem();                          /* 0x452580 */
    void OpenPaks(const std::string &name);  /* 0x451E90 */
    void *OpenFile(const std::string &name); /* 0x4514B0 */
};
static_assert(sizeof(CFileSystem) == 0xB8, "CFileSystem is 0xB8 bytes");
static_assert(__builtin_offsetof(CFileSystem, files) == 0x10, "CFileSystem::files");
static_assert(__builtin_offsetof(CFileSystem, streams) == 0x38, "CFileSystem::streams");
static_assert(__builtin_offsetof(CFileSystem, archiveName) == 0x60, "CFileSystem::archiveName");
static_assert(__builtin_offsetof(CFileSystem, paksOpened) == 0x7C, "CFileSystem::paksOpened");
static_assert(__builtin_offsetof(CFileSystem, currentStream) == 0x80, "CFileSystem::currentStream");
static_assert(__builtin_offsetof(CFileSystem, lastEntry) == 0x84, "CFileSystem::lastEntry");
static_assert(__builtin_offsetof(CFileSystem, embedded) == 0x88, "CFileSystem::embedded");
