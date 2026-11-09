/* CDatFile: the game's keyword database (0xBFC bytes, singleton 0x6C8E20).
 *
 * The file text is cached per file name in sources[] (up to 10, the loader 0x445AB0 reuses them), and the
 * tokenizer 0x445240 walks sources[currentSource].text from sourcePos. formatSets holds the keyword tables with
 * their format patterns ('w' a word, 'n' a number): set 0 (3 entries) fullscreen/resolution/texturequality,
 * set 1 (8 entries) the camera keys and gamepause/cameratoggle. The keyword reader 0x445DB0 fills records[]:
 * per record a counted array of std::string values and the matching float array; a counted array keeps its
 * count in the word before its first element. */
#pragma once
#include "game/common.h"

/* a cached source file and the read position in its text (one of the 10 at +24) */
struct DatSource {
    std::string name; /* +00 */
    std::string text; /* +1C */
    int pos;          /* +38 */
};
static_assert(sizeof(DatSource) == 0x3C, "DatSource is 0x3C bytes");

/* a keyword and its format pattern (a counted array element at +288/+28C) */
struct DatPair {
    std::string keyword; /* +00 */
    std::string format;  /* +1C */
};
static_assert(sizeof(DatPair) == 0x38, "DatPair is 0x38 bytes");

/* the arrays of one record (+298, 300 of them) */
struct DatRecord {
    std::string *words; /* +00 counted array of words: the count is at words[-1] */
    float *numbers;     /* +04 the numbers, matched position by position */
};
static_assert(sizeof(DatRecord) == 0x08, "DatRecord is 8 bytes");

struct CDatFile {
    void *vftable;          /* +000 CSingleton<CDatFile> */
    char token;             /* +004 the character the tokenizer last took */
    char pad005[3];
    std::string tokenText;  /* +008 the token being spelled */
    DatSource sources[10];  /* +024 */
    int sourceCount;        /* +27C number of cached sources (9 once the table is full) */
    int currentSource;      /* +280 the source the tokenizer reads */
    int formatSet;          /* +284 the keyword table in use (set by the reader 0x445DB0) */
    DatPair *formatSets[2]; /* +288 counted keyword tables: 3 entries and 8 entries */
    int keywordIndex;       /* +290 the keyword matched in the current set */
    unsigned sourcePos;     /* +294 the tokenizer position in the current source text */
    DatRecord records[300]; /* +298 */
    unsigned recordCount;   /* +BF8 */

    CDatFile();  /* 0x444D50 */
    ~CDatFile(); /* 0x445130 */

    bool LoadSource(const std::string &file);       /* 0x445AB0 caches the file text (or reuses a cached one) */
    void ReadChar();                                /* 0x445240 takes the next character of the current source */
    void ReadToken();                               /* 0x445C60 takes the next token into tokenText */
    bool SelectKeyword(const std::string &keyword); /* 0x445CD0 finds the keyword line ("#keyword") in the source */
};
static_assert(sizeof(CDatFile) == 0xBFC, "CDatFile is 0xBFC bytes");
static_assert(__builtin_offsetof(CDatFile, tokenText) == 0x008, "CDatFile::tokenText");
static_assert(__builtin_offsetof(CDatFile, sources) == 0x024, "CDatFile::sources");
static_assert(__builtin_offsetof(CDatFile, sourceCount) == 0x27C, "CDatFile::sourceCount");
static_assert(__builtin_offsetof(CDatFile, currentSource) == 0x280, "CDatFile::currentSource");
static_assert(__builtin_offsetof(CDatFile, formatSet) == 0x284, "CDatFile::formatSet");
static_assert(__builtin_offsetof(CDatFile, formatSets) == 0x288, "CDatFile::formatSets");
static_assert(__builtin_offsetof(CDatFile, keywordIndex) == 0x290, "CDatFile::keywordIndex");
static_assert(__builtin_offsetof(CDatFile, sourcePos) == 0x294, "CDatFile::sourcePos");
static_assert(__builtin_offsetof(CDatFile, records) == 0x298, "CDatFile::records");
static_assert(__builtin_offsetof(CDatFile, recordCount) == 0xBF8, "CDatFile::recordCount");
