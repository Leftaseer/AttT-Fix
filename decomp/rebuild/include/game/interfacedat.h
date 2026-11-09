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

/* The elements of the keyword lines: a name and a few strings and numbers in the order of the tokens. The
 * numbers after the 0x105 token (x2/y2 here) are an optional pair; the parser zeroes it when the token is
 * absent. Only the strings need construction, the numbers stay uninitialised until the parser fills them. */

/* keyword 0x143 element */
struct InterfaceItem4C {
    std::string name;      /* +000 lowercased */
    std::string text;      /* +01C */
    unsigned char flag;    /* +038 the low byte of the first number token */
    float x;               /* +03C */
    float y;               /* +040 */
    float x2;              /* +044 */
    float y2;              /* +048 */

    InterfaceItem4C() {} /* the parser's stack item: the strings start empty, the numbers fill later */
    InterfaceItem4C(const InterfaceItem4C &other); /* 0x421020 */
    void Read(); /* 0x4A1A60 */
};
static_assert(sizeof(InterfaceItem4C) == 0x4C, "InterfaceItem4C is 0x4C bytes");
static_assert(__builtin_offsetof(InterfaceItem4C, text) == 0x01C, "InterfaceItem4C::text");
static_assert(__builtin_offsetof(InterfaceItem4C, flag) == 0x038, "InterfaceItem4C::flag");
static_assert(__builtin_offsetof(InterfaceItem4C, x) == 0x03C, "InterfaceItem4C::x");
static_assert(__builtin_offsetof(InterfaceItem4C, x2) == 0x044, "InterfaceItem4C::x2");

/* keyword 0x144 element */
struct InterfaceItem48 {
    std::string name; /* +000 lowercased */
    std::string text; /* +01C */
    float x;          /* +038 */
    float y;          /* +03C */
    float x2;         /* +040 */
    float y2;         /* +044 */

    void Read(); /* 0x4A1B10 */
};
static_assert(sizeof(InterfaceItem48) == 0x48, "InterfaceItem48 is 0x48 bytes");
static_assert(__builtin_offsetof(InterfaceItem48, text) == 0x01C, "InterfaceItem48::text");
static_assert(__builtin_offsetof(InterfaceItem48, x) == 0x038, "InterfaceItem48::x");
static_assert(__builtin_offsetof(InterfaceItem48, x2) == 0x040, "InterfaceItem48::x2");

/* keyword 0x145 element */
struct InterfaceItem2C {
    std::string name; /* +000 */
    float x;          /* +01C */
    float y;          /* +020 */
    float x2;         /* +024 */
    float y2;         /* +028 */
};
static_assert(sizeof(InterfaceItem2C) == 0x2C, "InterfaceItem2C is 0x2C bytes");
static_assert(__builtin_offsetof(InterfaceItem2C, x) == 0x01C, "InterfaceItem2C::x");
static_assert(__builtin_offsetof(InterfaceItem2C, x2) == 0x024, "InterfaceItem2C::x2");

/* keyword 0x146 element */
struct InterfaceItem64 {
    std::string name;     /* +000 */
    float x;              /* +01C */
    float y;              /* +020 */
    unsigned char flag;   /* +024 the first character of its token */
    std::string text1;    /* +028 */
    float z;              /* +044 */
    std::string text2;    /* +048 */
};
static_assert(sizeof(InterfaceItem64) == 0x64, "InterfaceItem64 is 0x64 bytes");
static_assert(__builtin_offsetof(InterfaceItem64, flag) == 0x024, "InterfaceItem64::flag");
static_assert(__builtin_offsetof(InterfaceItem64, text1) == 0x028, "InterfaceItem64::text1");
static_assert(__builtin_offsetof(InterfaceItem64, z) == 0x044, "InterfaceItem64::z");
static_assert(__builtin_offsetof(InterfaceItem64, text2) == 0x048, "InterfaceItem64::text2");

/* keyword 0x14A element */
struct InterfaceItemE4 {
    std::string name;     /* +000 */
    float x;              /* +01C */
    float y;              /* +020 */
    unsigned char flag;   /* +024 the first character of its token */
    std::string text1;    /* +028 */
    float z;              /* +044 */
    std::string text2;    /* +048 */
    float u;              /* +064 */
    float v;              /* +068 */
    unsigned char flag2;  /* +06C the first character of its token */
    std::string text3;    /* +070 */
    float w;              /* +08C */
    std::string text4;    /* +090 */
    std::string text5;    /* +0AC */
    std::string text6;    /* +0C8 the name without its last character, lowercased */

    ~InterfaceItemE4(); /* 0x420F10 */
};
static_assert(sizeof(InterfaceItemE4) == 0xE4, "InterfaceItemE4 is 0xE4 bytes");
static_assert(__builtin_offsetof(InterfaceItemE4, flag) == 0x024, "InterfaceItemE4::flag");
static_assert(__builtin_offsetof(InterfaceItemE4, text1) == 0x028, "InterfaceItemE4::text1");
static_assert(__builtin_offsetof(InterfaceItemE4, text3) == 0x070, "InterfaceItemE4::text3");
static_assert(__builtin_offsetof(InterfaceItemE4, text6) == 0x0C8, "InterfaceItemE4::text6");

/* keyword 0x14C element */
struct InterfaceItem118 {
    std::string name;     /* +000 */
    float x;              /* +01C */
    float y;              /* +020 */
    unsigned char flag;   /* +024 the first character of its token */
    std::string text1;    /* +028 */
    float z;              /* +044 */
    std::string text2;    /* +048 */
    float u;              /* +064 */
    float v;              /* +068 */
    float w;              /* +06C */
    unsigned char flag2;  /* +070 the first character of its token */
    std::string text3;    /* +074 */
    float a;              /* +090 */
    std::string text4;    /* +094 */
    float b;              /* +0B0 */
    std::string text5;    /* +0B4 */
    float c;              /* +0D0 */
    float d;              /* +0D4 */
    unsigned char flag3;  /* +0D8 the first character of its token */
    std::string text6;    /* +0DC */
    float e;              /* +0F8 */
    std::string text7;    /* +0FC */

    ~InterfaceItem118(); /* 0x420F90 */
};
static_assert(sizeof(InterfaceItem118) == 0x118, "InterfaceItem118 is 0x118 bytes");
static_assert(__builtin_offsetof(InterfaceItem118, flag) == 0x024, "InterfaceItem118::flag");
static_assert(__builtin_offsetof(InterfaceItem118, text3) == 0x074, "InterfaceItem118::text3");
static_assert(__builtin_offsetof(InterfaceItem118, text7) == 0x0FC, "InterfaceItem118::text7");

/* an engine vector: an empty allocator and the three pointers. Its elements are the interface items above;
 * the range destroyers free their strings (0x422B90 / 0x422BF0 / 0x422C50) and the vector destructors
 * release the element buffer (0x497C10 / 0x423210 / 0x423260). */
struct InterfaceVector {
    unsigned char allocator[4]; /* +00 */
    void *begin;                /* +04 */
    void *end;                  /* +08 */
    void *limit;                /* +0C */

    void ReadItems64();  /* 0x4A6C00 keyword 0x146 */
    void ReadItemsE4();  /* 0x4A61C0 keyword 0x14A */
    void ReadItems118(); /* 0x4A63B0 keyword 0x14C */
};
static_assert(sizeof(InterfaceVector) == 0x10, "InterfaceVector is 0x10 bytes");

/* a titled vector: the keyword line gives the title, then the vector of the elements */
struct InterfaceCollection {
    std::string title;          /* +00 */
    unsigned char allocator[4]; /* +1C */
    void *begin;                /* +20 */
    void *end;                  /* +24 */
    void *limit;                /* +28 */

    void ReadItems4C(); /* 0x4A5F00 keyword 0x143 */
    void ReadItems48(); /* 0x4A5FD0 keyword 0x144 */
    void ReadItems2C(); /* 0x4A60A0 keyword 0x145 */
};
static_assert(sizeof(InterfaceCollection) == 0x2C, "InterfaceCollection is 0x2C bytes");
static_assert(__builtin_offsetof(InterfaceCollection, allocator) == 0x1C, "InterfaceCollection::allocator");

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

/* a node of the record map: the library's links, the key string and the record value (0x15C bytes) */
struct InterfaceRecordNode {
    InterfaceRecordNode *next; /* +00 */
    InterfaceRecordNode *prev; /* +04 */
    std::string key;           /* +08 */
    InterfaceRecord value;     /* +24 */
};
static_assert(sizeof(InterfaceRecordNode) == 0x15C, "InterfaceRecordNode is 0x15C bytes");
static_assert(__builtin_offsetof(InterfaceRecordNode, key) == 0x08, "InterfaceRecordNode::key");
static_assert(__builtin_offsetof(InterfaceRecordNode, value) == 0x24, "InterfaceRecordNode::value");

/* the record map: the same bucket map as CFileSystem's, but its sentinel is a whole record node */
InterfaceRecordNode *__stdcall CreateRecordNodeSentinel(); /* 0x4A2B40 */
FsHashMap *__thiscall InitRecordMap(FsHashMap *map, const unsigned char *allocator, const void *compare); /* 0x4A7040 */
void __fastcall ClearRecordNodeList(char *mapObject); /* 0x422AD0 the map's tree part (map + 4) */

struct CReadInterfaceDat {
    void *vftable; /* +00 CSingleton<CReadInterfaceDat> */
    FsHashMap map; /* +04 the loaded records */

    CReadInterfaceDat();                    /* 0x4A7160 */
    ~CReadInterfaceDat();                   /* 0x4A70C0 */
    void Load(const std::string &name);     /* 0x4A71E0 */
};
static_assert(sizeof(CReadInterfaceDat) == 0x2C, "CReadInterfaceDat is 0x2C bytes");
static_assert(__builtin_offsetof(CReadInterfaceDat, map) == 0x04, "CReadInterfaceDat::map");
