/* CReadTalkDat: the talk table of Talks.dat and its loader (0x4AB470 / 0x4AB4B0 / 0x4AB660), the 0xA4-byte
 * entries the file describes (0x4AA7E0 / 0x4AA570 / 0x4AA940 / 0x4AA870), the parser that fills them
 * (0x4AAB70) and the std::vector<TalkLine> / std::vector<TalkEntry> machinery the loader uses (0x4A99C0 ...
 * 0x4AB5C0).
 *
 * A file is a sequence of 0x150 blocks:
 *
 *   <id> <skipped> BLOCK_OPEN <flag> <text> <value> <text2>          (or 0x14E for the second block)
 *   ... a second such block, then lines: <kind> <text> ... up to BLOCK_CLOSE
 *
 * The parser starts every line with the 0x133/0x14E token that selects its kind and gives it a duration of
 * max(2 * strlen(text), 50).  The two blocks and the entry id are parsed before the lines. */
#pragma once
#include "game/common.h"

/* one line of a talk: the kind the 0x133/0x14E token selected, its text and how long it stays (ms) */
struct TalkLine {
    unsigned kind;      /* +00 */
    std::string text;   /* +04 */
    unsigned duration;  /* +20 */
};
static_assert(sizeof(TalkLine) == 0x24, "TalkLine is 0x24 bytes");
static_assert(__builtin_offsetof(TalkLine, text) == 0x04, "TalkLine::text");
static_assert(__builtin_offsetof(TalkLine, duration) == 0x20, "TalkLine::duration");

/* one of the two first-block/second-block records of an entry: two floats and a byte that the parser reads,
 * then two texts around a number */
struct TalkBlock {
    float x;            /* +00 */
    float y;            /* +04 */
    bool flag;          /* +08 */
    std::string text;   /* +0C */
    float value;        /* +28 */
    std::string text2;  /* +2C */
};
static_assert(sizeof(TalkBlock) == 0x48, "TalkBlock is 0x48 bytes");
static_assert(__builtin_offsetof(TalkBlock, flag) == 0x08, "TalkBlock::flag");
static_assert(__builtin_offsetof(TalkBlock, text) == 0x0C, "TalkBlock::text");
static_assert(__builtin_offsetof(TalkBlock, value) == 0x28, "TalkBlock::value");
static_assert(__builtin_offsetof(TalkBlock, text2) == 0x2C, "TalkBlock::text2");

/* std::vector<TalkLine> as the original lays it out: the empty allocator, then the three pointers.  The code
 * only ever touches the pointers, so the allocator keeps whatever the owner's memory held. */
struct TalkLineVector {
    unsigned allocator; /* +00 */
    TalkLine *begin;    /* +04 */
    TalkLine *end;      /* +08 */
    TalkLine *limit;    /* +0C */
};
static_assert(sizeof(TalkLineVector) == 0x10, "TalkLineVector is 0x10 bytes");

/* std::vector<TalkEntry> (the same layout) */
struct TalkEntry;
struct TalkEntryVector {
    unsigned allocator; /* +00 */
    TalkEntry *begin;   /* +04 */
    TalkEntry *end;     /* +08 */
    TalkEntry *limit;   /* +0C */
};
static_assert(sizeof(TalkEntryVector) == 0x10, "TalkEntryVector is 0x10 bytes");

/* one talk: its id, the two blocks and the lines */
struct TalkEntry {
    unsigned id;              /* +00 */
    TalkBlock first;          /* +04 */
    TalkBlock second;         /* +4C */
    TalkLineVector lines;     /* +94 */
};
static_assert(sizeof(TalkEntry) == 0xA4, "TalkEntry is 0xA4 bytes");
static_assert(__builtin_offsetof(TalkEntry, first) == 0x04, "TalkEntry::first");
static_assert(__builtin_offsetof(TalkEntry, second) == 0x4C, "TalkEntry::second");
static_assert(__builtin_offsetof(TalkEntry, lines) == 0x94, "TalkEntry::lines");

/* a block's lifetime: the two strings copy-construct/assign and the flag byte is copied as it is */
TalkBlock *__thiscall CopyConstructTalkBlock(TalkBlock *block, const TalkBlock *other); /* 0x421150 */
void __fastcall DestroyTalkBlock(TalkBlock *block);                                     /* 0x420910 */

/* TalkLine storage and the four element loops (copy construct, fill construct, copy assign, fill assign,
 * copy backward, destroy), plus the vector algorithms built on them */
TalkLine *__cdecl AllocateTalkLines(unsigned count);                                      /* 0x4A99C0 */
TalkLine *__cdecl CopyConstructTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst); /* 0x4A9DE0 */
void __cdecl FillConstructTalkLines(TalkLine *dst, unsigned count, const TalkLine *value); /* 0x4A9E80 */
TalkLine *__stdcall FillConstructTalkLinesEnd(TalkLine *dst, unsigned count,
                                              const TalkLine *value);                     /* 0x4AA010 */
TalkLine *__cdecl CopyAssignTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst);    /* 0x4A9C10 */
void __cdecl FillAssignTalkLines(TalkLine *first, TalkLine *last, const TalkLine *value); /* 0x4A9C60 */
TalkLine *__cdecl CopyBackwardTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst);  /* 0x4A9AB0 */
void __stdcall DestroyTalkLines(TalkLine *first, TalkLine *last);                         /* 0x4AA050 */

void __thiscall EraseTalkLines(TalkLineVector *vector, TalkLine **result, TalkLine *first,
                               TalkLine *last);                                           /* 0x4AA0B0 */
void __fastcall DestroyTalkLineVector(TalkLineVector *vector);                            /* 0x4AA120 */
TalkLineVector *__thiscall CopyConstructTalkLineVector(TalkLineVector *vector,
                                                       const TalkLineVector *other);      /* 0x4AA170 */
void __fastcall ClearTalkLineVector(TalkLineVector *vector);                              /* 0x4AA250 */
void __thiscall InsertTalkLines(TalkLineVector *vector, TalkLine *position, unsigned count,
                                const TalkLine *value);                                   /* 0x4AA270 */
void __thiscall InsertTalkLineAt(TalkLineVector *vector, TalkLine **result, TalkLine *position,
                                 const TalkLine *value);                                  /* 0x4AA8D0 */
void __thiscall PushTalkLine(TalkLineVector *vector, const TalkLine *value);              /* 0x4AAA80 */

/* TalkEntry storage and the same element loops (the vector of lines is copied with its own algorithms) */
TalkEntry *__cdecl AllocateTalkEntries(unsigned count);                                    /* 0x4A9A20 */
TalkEntry *__thiscall CopyConstructTalkEntry(TalkEntry *entry, const TalkEntry *other);    /* 0x4AA570 */
TalkEntry *__thiscall AssignTalkEntry(TalkEntry *entry, const TalkEntry *other);           /* 0x4AA940 */
TalkLineVector *__thiscall AssignTalkLineVector(TalkLineVector *vector,
                                                const TalkLineVector *other);              /* 0x4AA5F0 */
TalkEntry *__fastcall ConstructTalkEntry(TalkEntry *entry);                               /* 0x4AA7E0 */
void __fastcall DestroyTalkEntry(TalkEntry *entry);                                       /* 0x4AA870 */
TalkEntry *__cdecl CopyConstructTalkEntries(TalkEntry *first, TalkEntry *last,
                                            TalkEntry *dst);                              /* 0x4AAD90 */
void __cdecl FillConstructTalkEntries(TalkEntry *dst, unsigned count,
                                      const TalkEntry *value);                            /* 0x4AAE30 */
TalkEntry *__cdecl CopyBackwardTalkEntries(TalkEntry *first, TalkEntry *last,
                                           TalkEntry *dst);                               /* 0x4AAA20 */
void __cdecl FillAssignTalkEntries(TalkEntry *first, TalkEntry *last,
                                   const TalkEntry *value);                               /* 0x4AAB10 */
void __cdecl DestroyTalkEntries(TalkEntry *first, TalkEntry *last);                       /* 0x4AAED0 */
void __fastcall DestroyTalkEntryVector(TalkEntryVector *vector);                          /* 0x4AB100 */
void __thiscall InsertTalkEntries(TalkEntryVector *vector, TalkEntry *position, unsigned count,
                                  const TalkEntry *value);                                /* 0x4AB170 */
void __thiscall InsertTalkEntryAt(TalkEntryVector *vector, TalkEntry **result,
                                  TalkEntry *position, const TalkEntry *value);            /* 0x4AB530 */
void __thiscall PushTalkEntry(TalkEntryVector *vector, const TalkEntry *value);           /* 0x4AB5C0 */

void __fastcall ParseTalkEntry(TalkEntry *entry); /* 0x4AAB70 */

/* the singleton the game keeps: the loaded talks behind the class vtable */
struct CReadTalkDat {
    void *vftable;          /* +00 CSingleton<CReadTalkDat>, 0x61015C while the class is alive */
    TalkEntryVector talks;  /* +04 */

    CReadTalkDat();  /* 0x4AB470 */
    ~CReadTalkDat(); /* 0x4AB4B0 */
    void Load();     /* 0x4AB660 */
};
static_assert(sizeof(CReadTalkDat) == 0x14, "CReadTalkDat is 0x14 bytes");
static_assert(__builtin_offsetof(CReadTalkDat, talks) == 0x04, "CReadTalkDat::talks");
