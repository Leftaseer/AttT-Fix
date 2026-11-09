/* CReadInterfaceDat: the table of interface records (0x2C bytes, singleton 0x6C8680).
 *
 * The loader 0x4A71E0 reads the game's interface dat file into a map<string, entry> at +04; the map is the same
 * 0x28-byte engine map CFileSystem uses (FsHashMap): a record is found by its name.
 *
 * Each entry is an InterfaceRecord (0x138 bytes): the parser 0x4A6D30 fills it keyword by keyword (the numbers
 * of the members are the keyword tokens the parser 0x470410 returns), and the map keys it by its first string. */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

/* an engine vector: an empty allocator and the three pointers. Its elements are game structures the record keeps
 * opaque (their destructors are the originals at 0x422B90 / 0x422BF0 / 0x422C50 / 0x420F10 / 0x420F90). */
struct InterfaceVector {
    unsigned char allocator[4]; /* +00 */
    void *begin;                /* +04 */
    void *end;                  /* +08 */
    void *limit;                /* +0C */
};
static_assert(sizeof(InterfaceVector) == 0x10, "InterfaceVector is 0x10 bytes");

/* a titled vector: the keyword line gives the title, then the vector of the elements */
struct InterfaceCollection {
    std::string title;          /* +00 */
    unsigned char allocator[4]; /* +1C */
    void *begin;                /* +20 */
    void *end;                  /* +24 */
    void *limit;                /* +28 */
};
static_assert(sizeof(InterfaceCollection) == 0x2C, "InterfaceCollection is 0x2C bytes");

/* One record of the interface dat. The parser keywords: 0x142 two strings ("text142"), 0x143/0x144/0x145 three
 * titled vectors, 0x146 a vector, 0x147 a string, 0x149 four floats (x, y and optionally x2, y2), 0x14A/0x14C two
 * more vectors and 0x14B one float. */
struct InterfaceRecord {
    std::string name;             /* +000 the map key */
    std::string text142[2];       /* +01C keyword 0x142: two strings */
    InterfaceCollection items143; /* +054 keyword 0x143 */
    InterfaceCollection items144; /* +080 keyword 0x144 */
    InterfaceCollection items145; /* +0AC keyword 0x145 */
    InterfaceVector items146;     /* +0D8 keyword 0x146 */
    std::string text147;          /* +0E8 keyword 0x147 */
    float number14B;              /* +104 keyword 0x14B */
    float floats149[4];           /* +108 keyword 0x149: x, y and optionally x2, y2 */
    InterfaceVector items14A;     /* +118 keyword 0x14A */
    InterfaceVector items14C;     /* +128 keyword 0x14C */

    InterfaceRecord();                            /* 0x4A6610 */
    ~InterfaceRecord();                           /* 0x4A6740 */
    InterfaceRecord &operator=(const InterfaceRecord &other); /* 0x4A6E90 */
    void Read();                                  /* 0x4A6D30 reads the record's keywords from the lexer */
};
static_assert(sizeof(InterfaceRecord) == 0x138, "InterfaceRecord is 0x138 bytes");
static_assert(__builtin_offsetof(InterfaceRecord, text142) == 0x01C, "InterfaceRecord::text142");
static_assert(__builtin_offsetof(InterfaceRecord, items143) == 0x054, "InterfaceRecord::items143");
static_assert(__builtin_offsetof(InterfaceRecord, items144) == 0x080, "InterfaceRecord::items144");
static_assert(__builtin_offsetof(InterfaceRecord, items145) == 0x0AC, "InterfaceRecord::items145");
static_assert(__builtin_offsetof(InterfaceRecord, items146) == 0x0D8, "InterfaceRecord::items146");
static_assert(__builtin_offsetof(InterfaceRecord, text147) == 0x0E8, "InterfaceRecord::text147");
static_assert(__builtin_offsetof(InterfaceRecord, number14B) == 0x104, "InterfaceRecord::number14B");
static_assert(__builtin_offsetof(InterfaceRecord, floats149) == 0x108, "InterfaceRecord::floats149");
static_assert(__builtin_offsetof(InterfaceRecord, items14A) == 0x118, "InterfaceRecord::items14A");
static_assert(__builtin_offsetof(InterfaceRecord, items14C) == 0x128, "InterfaceRecord::items14C");

struct CReadInterfaceDat {
    void *vftable; /* +00 CSingleton<CReadInterfaceDat> */
    FsHashMap map; /* +04 the loaded records */

    CReadInterfaceDat();                    /* 0x4A7160 */
    ~CReadInterfaceDat();                   /* 0x4A70C0 */
    void Load(const std::string &name);     /* 0x4A71E0 */
};
static_assert(sizeof(CReadInterfaceDat) == 0x2C, "CReadInterfaceDat is 0x2C bytes");
static_assert(__builtin_offsetof(CReadInterfaceDat, map) == 0x04, "CReadInterfaceDat::map");
