/* CReadTalkDat: the talk table of Talks.dat - the vector<TalkLine> and vector<TalkEntry> operations the loader
 * uses (0x4A99C0 ... 0x4AB5C0), the entry parser (0x4AAB70) and the loader object (0x4AB470 / 0x4AB4B0 /
 * 0x4AB660).  The macros and the scanner are the ones of the other dat loaders. */
#include "game/common.h"
#include "game/talkdat.h"
#include "game/gamefile.h"
#include "game/datlexer.h"
#include "game/fsarchive.h"

ORIG_DATA(0061015C); /* CReadTalkDat::vftable */
ORIG_DATA(00610154); /* CSingleton<CReadTalkDat>::vftable */
ORIG_DATA(00610160); /* "Talks.dat" */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006CA2C0); /* the token the talk parser read last */
ORIG_DATA(006C9060); /* the numeric value of the last token (a float) */
ORIG_DATA(006C9068); /* the text of the last token */

inline void *operator new(unsigned int, void *p) { return p; }

/* the size guards of the two vectors: count * 0x24 and count * 0xa4 elements */
static const unsigned kMaxTalkLines = 0x71C71C7u;
static const unsigned kMaxTalkEntries = 0x18F9C18u;

/* --- vector<TalkLine> storage ------------------------------------------------------------------------- */

/* The line vectors allocate through operator new; the huge-count guard of _Buy is the same length_error. */
DECOMP(004A99C0)
TalkLine *__cdecl AllocateTalkLines(unsigned count)
{
    if (count != 0 && 0xFFFFFFFFu / count < sizeof(TalkLine))
        ThrowVectorLengthError();
    return (TalkLine *)operator new(count * sizeof(TalkLine));
}

DECOMP(004A9A20)
TalkEntry *__cdecl AllocateTalkEntries(unsigned count)
{
    if (count != 0 && 0xFFFFFFFFu / count < sizeof(TalkEntry))
        ThrowVectorLengthError();
    return (TalkEntry *)operator new(count * sizeof(TalkEntry));
}

/* Copy-constructs the lines [first, last) at dst and returns the position after them. */
DECOMP(004A9DE0)
TalkLine *__cdecl CopyConstructTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst)
{
    for (; first != last; ++first, ++dst)
        new (dst) TalkLine(*first);
    return dst;
}

/* Constructs count copies of value at dst. */
DECOMP(004A9E80)
void __cdecl FillConstructTalkLines(TalkLine *dst, unsigned count, const TalkLine *value)
{
    for (; count != 0; --count, ++dst)
        new (dst) TalkLine(*value);
}

/* The fill that reports the end position (the wrapper the insertion algorithms use). */
DECOMP(004AA010)
TalkLine *__stdcall FillConstructTalkLinesEnd(TalkLine *dst, unsigned count, const TalkLine *value)
{
    FillConstructTalkLines(dst, count, value);
    return dst + count;
}

/* Assigns the lines [first, last) over dst and returns the position after them. */
DECOMP(004A9C10)
TalkLine *__cdecl CopyAssignTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst)
{
    for (; first != last; ++first, ++dst)
        *dst = *first;
    return dst;
}

/* Assigns copies of value over [first, last). */
DECOMP(004A9C60)
void __cdecl FillAssignTalkLines(TalkLine *first, TalkLine *last, const TalkLine *value)
{
    for (; first != last; ++first)
        *first = *value;
}

/* std::copy_backward for lines: the last line is assigned first. */
DECOMP(004A9AB0)
TalkLine *__cdecl CopyBackwardTalkLines(TalkLine *first, TalkLine *last, TalkLine *dst)
{
    while (first != last) {
        --last;
        --dst;
        *dst = *last;
    }
    return dst;
}

DECOMP(004AA050)
void __stdcall DestroyTalkLines(TalkLine *first, TalkLine *last)
{
    for (; first != last; ++first)
        first->~TalkLine();
}

/* --- vector<TalkLine> --------------------------------------------------------------------------------- */

/* vector::erase(first, last): the tail after last moves down over the erased range and the end follows it;
 * the new position of first comes back through result. */
DECOMP(004AA0B0)
void __thiscall EraseTalkLines(TalkLineVector *vector, TalkLine **result, TalkLine *first, TalkLine *last)
{
    if (first != last) {
        TalkLine *end = vector->end;
        TalkLine *newEnd = CopyAssignTalkLines(last, end, first);
        for (TalkLine *it = newEnd; it != end; ++it)
            it->~TalkLine();
        vector->end = newEnd;
    }
    *result = first;
}

/* vector's lifetime: the elements are destroyed, the block freed and the three pointers cleared; the
 * allocator dword stays as the owner left it. */
DECOMP(004AA120)
void __fastcall DestroyTalkLineVector(TalkLineVector *vector)
{
    if (vector->begin != nullptr) {
        DestroyTalkLines(vector->begin, vector->end);
        operator delete(vector->begin);
    }
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
}

/* vector's copy constructor: a fresh block copies the source lines, and an empty source leaves the vector
 * empty (it does not copy the allocator). */
DECOMP(004AA170)
TalkLineVector *__thiscall CopyConstructTalkLineVector(TalkLineVector *vector, const TalkLineVector *other)
{
    unsigned count = other->begin ? (unsigned)(other->end - other->begin) : 0;
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
    if (count != 0) {
        if (count > kMaxTalkLines)
            ThrowVectorLengthError();
        TalkLine *data = AllocateTalkLines(count);
        vector->limit = data + count;
        vector->begin = data;
        vector->end = CopyConstructTalkLines(other->begin, other->end, data);
    }
    return vector;
}

/* vector::clear() through the erase above */
DECOMP(004AA250)
void __fastcall ClearTalkLineVector(TalkLineVector *vector)
{
    TalkLine *result;
    EraseTalkLines(vector, &result, vector->begin, vector->end);
}

/* vector::_Insert_n: count copies of value go in at position.  The value is copied to a stack temporary
 * first, because it may point into the vector the reallocation below frees.  A short capacity grows to half
 * again as much (or to the new size), moves the two ranges around the new lines and frees the old block;
 * otherwise the tail either moves after the new lines when it is shorter than count, or its last count
 * lines move first into the grown raw tail and the middle shifts over the filled range. */
DECOMP(004AA270)
void __thiscall InsertTalkLines(TalkLineVector *vector, TalkLine *position, unsigned count,
                                const TalkLine *value)
{
    TalkLine temporary(*value);
    if (count == 0)
        return;

    TalkLine *begin = vector->begin;
    TalkLine *end = vector->end;
    unsigned size = begin ? (unsigned)(end - begin) : 0;
    unsigned capacity = begin ? (unsigned)(vector->limit - begin) : 0;
    if (size > kMaxTalkLines - count)
        ThrowVectorLengthError();

    if (capacity < size + count) {
        unsigned grown = capacity > kMaxTalkLines - capacity / 2 ? 0 : capacity + capacity / 2;
        if (grown < size + count)
            grown = size + count;
        TalkLine *data = AllocateTalkLines(grown);
        TalkLine *dst = CopyConstructTalkLines(begin, position, data);
        dst = FillConstructTalkLinesEnd(dst, count, &temporary);
        dst = CopyConstructTalkLines(position, end, dst);
        if (begin != nullptr) {
            DestroyTalkLines(begin, end);
            operator delete(begin);
        }
        vector->limit = data + grown;
        vector->end = data + size + count;
        vector->begin = data;
        return;
    }

    unsigned tail = (unsigned)(end - position);
    if (tail < count) {
        CopyConstructTalkLines(position, end, position + count);
        FillConstructTalkLinesEnd(end, count - tail, &temporary);
        vector->end = end + count;
        FillAssignTalkLines(position, end, &temporary);
        return;
    }

    CopyConstructTalkLines(end - count, end, end);
    vector->end = end + count;
    CopyBackwardTalkLines(position, end - count, end);
    FillAssignTalkLines(position, position + count, &temporary);
}

/* vector::insert(position, 1, value) as the push path calls it: the returned iterator is the new element. */
DECOMP(004AA8D0)
void __thiscall InsertTalkLineAt(TalkLineVector *vector, TalkLine **result, TalkLine *position,
                                 const TalkLine *value)
{
    TalkLine *begin = vector->begin;
    unsigned index = 0;
    if (begin != nullptr && vector->end != begin)
        index = (unsigned)(position - begin);
    InsertTalkLines(vector, position, 1, value);
    *result = vector->begin + index;
}

/* vector::push_back: a spare slot constructs the line in place, otherwise the insertion above runs with the
 * end as the position. */
DECOMP(004AAA80)
void __thiscall PushTalkLine(TalkLineVector *vector, const TalkLine *value)
{
    TalkLine *begin = vector->begin;
    if (begin != nullptr && (unsigned)(vector->end - begin) < (unsigned)(vector->limit - begin)) {
        FillConstructTalkLines(vector->end, 1, value);
        vector->end += 1;
        return;
    }
    TalkLine *result;
    InsertTalkLineAt(vector, &result, vector->end, value);
}

/* --- vector<TalkEntry> elements ------------------------------------------------------------------------ */

/* A block copies the two numbers and the raw flag byte, then copy-constructs its two texts. */
DECOMP(00421150)
TalkBlock *__thiscall CopyConstructTalkBlock(TalkBlock *block, const TalkBlock *other)
{
    block->x = other->x;
    block->y = other->y;
    *(char *)&block->flag = *(const char *)&other->flag;
    new (&block->text) std::string(other->text);
    block->value = other->value;
    new (&block->text2) std::string(other->text2);
    return block;
}

/* A block's lifetime: the second text first, then the first. */
DECOMP(00420910)
void __fastcall DestroyTalkBlock(TalkBlock *block)
{
    block->text2.~basic_string();
    block->text.~basic_string();
}

/* The entry copies its id, the two blocks and the line vector; the blocks' strings copy-construct, the
 * line vector copies its own block. */
DECOMP(004AA570)
TalkEntry *__thiscall CopyConstructTalkEntry(TalkEntry *entry, const TalkEntry *other)
{
    entry->id = other->id;
    CopyConstructTalkBlock(&entry->first, &other->first);
    CopyConstructTalkBlock(&entry->second, &other->second);
    CopyConstructTalkLineVector(&entry->lines, &other->lines);
    return entry;
}

/* The entry assignment copies the fields in place: the numbers, the raw flag bytes, the assigned texts and
 * finally the line vector. */
DECOMP(004AA940)
TalkEntry *__thiscall AssignTalkEntry(TalkEntry *entry, const TalkEntry *other)
{
    entry->id = other->id;
    entry->first.x = other->first.x;
    entry->first.y = other->first.y;
    *(char *)&entry->first.flag = *(const char *)&other->first.flag;
    entry->first.text = other->first.text;
    entry->first.value = other->first.value;
    entry->first.text2 = other->first.text2;
    entry->second.x = other->second.x;
    entry->second.y = other->second.y;
    *(char *)&entry->second.flag = *(const char *)&other->second.flag;
    entry->second.text = other->second.text;
    entry->second.value = other->second.value;
    entry->second.text2 = other->second.text2;
    AssignTalkLineVector(&entry->lines, &other->lines);
    return entry;
}

/* vector<TalkLine>::operator=: an empty source clears the vector; a source no longer than the vector is
 * assigned over the prefix and the extra lines are destroyed; a longer source either fits the spare
 * capacity (the prefix is assigned and the rest constructed after the end) or takes a new block. */
DECOMP(004AA5F0)
TalkLineVector *__thiscall AssignTalkLineVector(TalkLineVector *vector, const TalkLineVector *other)
{
    if (vector == other)
        return vector;

    unsigned count = other->begin ? (unsigned)(other->end - other->begin) : 0;
    if (count == 0) {
        ClearTalkLineVector(vector);
        return vector;
    }

    TalkLine *begin = vector->begin;
    unsigned size = begin ? (unsigned)(vector->end - begin) : 0;
    if (count <= size) {
        TalkLine *newEnd = CopyAssignTalkLines(other->begin, other->end, begin);
        DestroyTalkLines(newEnd, vector->end);
        vector->end = newEnd;
        return vector;
    }

    unsigned capacity = begin ? (unsigned)(vector->limit - begin) : 0;
    if (capacity < count) {
        if (begin != nullptr) {
            DestroyTalkLines(begin, vector->end);
            operator delete(begin);
        }
        TalkLine *data = AllocateTalkLines(count);
        vector->begin = data;
        vector->end = data;
        vector->limit = data + count;
        vector->end = CopyConstructTalkLines(other->begin, other->end, data);
        return vector;
    }

    TalkLine *middle = other->begin + size;
    CopyAssignTalkLines(other->begin, middle, begin);
    vector->end = CopyConstructTalkLines(middle, other->end, vector->end);
    return vector;
}

/* The default entry of the loader: the four texts are constructed empty and the line vector starts empty;
 * the id and the blocks' numbers keep whatever the memory held. */
DECOMP(004AA7E0)
TalkEntry *__fastcall ConstructTalkEntry(TalkEntry *entry)
{
    new (&entry->first.text) std::string();
    new (&entry->first.text2) std::string();
    new (&entry->second.text) std::string();
    new (&entry->second.text2) std::string();
    entry->lines.begin = nullptr;
    entry->lines.end = nullptr;
    entry->lines.limit = nullptr;
    return entry;
}

/* The entry's lifetime: the line vector first (the block is freed), then the two texts of the second block
 * and the two of the first. */
DECOMP(004AA870)
void __fastcall DestroyTalkEntry(TalkEntry *entry)
{
    DestroyTalkLineVector(&entry->lines);
    DestroyTalkBlock(&entry->second);
    DestroyTalkBlock(&entry->first);
}

/* --- vector<TalkEntry> -------------------------------------------------------------------------------- */

/* Copy-constructs the entries [first, last) at dst and returns the position after them. */
DECOMP(004AAD90)
TalkEntry *__cdecl CopyConstructTalkEntries(TalkEntry *first, TalkEntry *last, TalkEntry *dst)
{
    for (; first != last; ++first, ++dst)
        CopyConstructTalkEntry(dst, first);
    return dst;
}

/* Constructs count copies of value at dst. */
DECOMP(004AAE30)
void __cdecl FillConstructTalkEntries(TalkEntry *dst, unsigned count, const TalkEntry *value)
{
    for (; count != 0; --count, ++dst)
        CopyConstructTalkEntry(dst, value);
}

/* std::copy_backward for entries (assignment, like the line version). */
DECOMP(004AAA20)
TalkEntry *__cdecl CopyBackwardTalkEntries(TalkEntry *first, TalkEntry *last, TalkEntry *dst)
{
    while (first != last) {
        --last;
        --dst;
        AssignTalkEntry(dst, last);
    }
    return dst;
}

/* Assigns copies of value over [first, last). */
DECOMP(004AAB10)
void __cdecl FillAssignTalkEntries(TalkEntry *first, TalkEntry *last, const TalkEntry *value)
{
    for (; first != last; ++first)
        AssignTalkEntry(first, value);
}

DECOMP(004AAED0)
void __cdecl DestroyTalkEntries(TalkEntry *first, TalkEntry *last)
{
    for (; first != last; ++first)
        DestroyTalkEntry(first);
}

/* vector's lifetime: the entries are destroyed, the block freed and the three pointers cleared. */
DECOMP(004AB100)
void __fastcall DestroyTalkEntryVector(TalkEntryVector *vector)
{
    if (vector->begin != nullptr) {
        DestroyTalkEntries(vector->begin, vector->end);
        operator delete(vector->begin);
    }
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
}

/* vector<TalkEntry>::_Insert_n - the line insertion above with 0xa4-byte elements.  The value is copied to
 * a stack temporary first so that it may point into the block being reallocated. */
DECOMP(004AB170)
void __thiscall InsertTalkEntries(TalkEntryVector *vector, TalkEntry *position, unsigned count,
                                  const TalkEntry *value)
{
    alignas(TalkEntry) unsigned char temporaryStorage[sizeof(TalkEntry)];
    TalkEntry *temporary = (TalkEntry *)temporaryStorage;
    CopyConstructTalkEntry(temporary, value);
    if (count == 0) {
        DestroyTalkEntry(temporary);
        return;
    }

    TalkEntry *begin = vector->begin;
    TalkEntry *end = vector->end;
    unsigned size = begin ? (unsigned)(end - begin) : 0;
    unsigned capacity = begin ? (unsigned)(vector->limit - begin) : 0;
    if (size > kMaxTalkEntries - count) {
        DestroyTalkEntry(temporary);
        ThrowVectorLengthError();
    }

    if (capacity < size + count) {
        unsigned grown = capacity > kMaxTalkEntries - capacity / 2 ? 0 : capacity + capacity / 2;
        if (grown < size + count)
            grown = size + count;
        TalkEntry *data = AllocateTalkEntries(grown);
        TalkEntry *dst = CopyConstructTalkEntries(begin, position, data);
        FillConstructTalkEntries(dst, count, temporary);
        dst += count;
        dst = CopyConstructTalkEntries(position, end, dst);
        if (begin != nullptr) {
            DestroyTalkEntries(begin, end);
            operator delete(begin);
        }
        vector->limit = data + grown;
        vector->end = data + size + count;
        vector->begin = data;
        DestroyTalkEntry(temporary);
        return;
    }

    unsigned tail = (unsigned)(end - position);
    if (tail < count) {
        CopyConstructTalkEntries(position, end, position + count);
        FillConstructTalkEntries(end, count - tail, temporary);
        vector->end = end + count;
        FillAssignTalkEntries(position, end, temporary);
        DestroyTalkEntry(temporary);
        return;
    }

    CopyConstructTalkEntries(end - count, end, end);
    vector->end = end + count;
    CopyBackwardTalkEntries(position, end - count, end);
    FillAssignTalkEntries(position, position + count, temporary);
    DestroyTalkEntry(temporary);
}

/* vector::insert(position, 1, value) as the push path calls it: the returned iterator is the new entry. */
DECOMP(004AB530)
void __thiscall InsertTalkEntryAt(TalkEntryVector *vector, TalkEntry **result, TalkEntry *position,
                                  const TalkEntry *value)
{
    TalkEntry *begin = vector->begin;
    unsigned index = 0;
    if (begin != nullptr && vector->end != begin)
        index = (unsigned)(position - begin);
    InsertTalkEntries(vector, position, 1, value);
    *result = vector->begin + index;
}

/* vector::push_back for entries */
DECOMP(004AB5C0)
void __thiscall PushTalkEntry(TalkEntryVector *vector, const TalkEntry *value)
{
    TalkEntry *begin = vector->begin;
    if (begin != nullptr && (unsigned)(vector->end - begin) < (unsigned)(vector->limit - begin)) {
        FillConstructTalkEntries(vector->end, 1, value);
        vector->end += 1;
        return;
    }
    TalkEntry *result;
    InsertTalkEntryAt(vector, &result, vector->end, value);
}

/* --- the parser and the loader ------------------------------------------------------------------------ */

/* Reads one 0x150 block: the id, a skipped token, the two 0x133/0x14E blocks (flag byte, text, number,
 * text) and then the lines.  Every line starts with the 0x133/0x14E token that selects its kind and ends
 * where the block closes; its duration is twice its length, at least 50.  The token cache is the global the
 * scanner's callers keep. */
DECOMP(004AAB70)
void __fastcall ParseTalkEntry(TalkEntry *entry)
{
    ClearTalkLineVector(&entry->lines);

    DatLexerNextToken();
    entry->id = (unsigned)(int)ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    for (int block = 0; block < 2; block++) {
        int token = DatLexerNextToken();
        ORIG_VAR(006CA2C0, int) = token;
        if (token == 0x133) {
            DatLexerNextToken();
            *(char *)&entry->first.flag = ORIG_VAR(006C9068, char);
            DatLexerNextToken();
            entry->first.text = (const char *)d_006C9068;
            DatLexerNextToken();
            entry->first.value = ORIG_VAR(006C9060, float);
            DatLexerNextToken();
            entry->first.text2 = (const char *)d_006C9068;
        } else if (token == 0x14E) {
            DatLexerNextToken();
            *(char *)&entry->second.flag = ORIG_VAR(006C9068, char);
            DatLexerNextToken();
            entry->second.text = (const char *)d_006C9068;
            DatLexerNextToken();
            entry->second.value = ORIG_VAR(006C9060, float);
            DatLexerNextToken();
            entry->second.text2 = (const char *)d_006C9068;
        }
    }

    ORIG_VAR(006CA2C0, int) = DatLexerNextToken();
    TalkLine line;
    do {
        if (ORIG_VAR(006CA2C0, int) == 0x133) {
            line.kind = 0;
            DatLexerNextToken();
        } else if (ORIG_VAR(006CA2C0, int) == 0x14E) {
            line.kind = 1;
            DatLexerNextToken();
        }
        line.text = (const char *)d_006C9068;
        unsigned duration = (unsigned)strlen(d_006C9068) * 2;
        line.duration = duration < 0x32 ? 0x32 : duration;
        PushTalkLine(&entry->lines, &line);
        ORIG_VAR(006CA2C0, int) = DatLexerNextToken();
    } while (ORIG_VAR(006CA2C0, int) != 0x103);
}

/* The loader's constructor: the class vtable and an empty vector.  The original leaves EDX alone (the symbol
 * table says only EAX and ECX change), so it is saved around the stores. */
DECOMP(004AB470)
CReadTalkDat::CReadTalkDat()
{
    unsigned savedEdx;
    __asm__ __volatile__("movl %%edx, %0" : "=m"(savedEdx));
    vftable = d_0061015C;
    talks.begin = nullptr;
    talks.end = nullptr;
    talks.limit = nullptr;
    __asm__ __volatile__("movl %0, %%edx" : : "m"(savedEdx));
}

/* The loader's destructor: the class vtable, the talks' entries freed and the vector cleared, then the
 * singleton vtable of the base. */
DECOMP(004AB4B0)
CReadTalkDat::~CReadTalkDat()
{
    vftable = d_0061015C;
    if (talks.begin != nullptr) {
        DestroyTalkEntries(talks.begin, talks.end);
        operator delete(talks.begin);
    }
    talks.begin = nullptr;
    talks.end = nullptr;
    talks.limit = nullptr;
    vftable = d_00610154;
}

/* Opens Talks.dat through the shared CGameFile, remembers the file size for the lexer, and pushes every
 * 0x150 block the parser reads until the end of the file. */
DECOMP(004AB660)
void CReadTalkDat::Load()
{
    CGameFile *reader = (CGameFile *)d_006CA280;
    {
        std::string name(ORIG_STR(00610160));
        reader->Open(name, 1);
    }
    ORIG_VAR(006CA278, unsigned) = reader->file->size;

    alignas(TalkEntry) unsigned char entryStorage[sizeof(TalkEntry)];
    TalkEntry *entry = (TalkEntry *)entryStorage;
    ConstructTalkEntry(entry);
    ORIG_VAR(006CA2C0, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2C0, int) != 0) {
        if (ORIG_VAR(006CA2C0, int) == 0x150) {
            ParseTalkEntry(entry);
            PushTalkEntry(&talks, entry);
        }
        ORIG_VAR(006CA2C0, int) = DatLexerNextToken();
    }
    reader->Close();
    DestroyTalkEntry(entry);
}
