/* CReadInputCfg: the input.cfg key/value list - the vector<CfgPair> machinery (0x4A0BA0 ... 0x4A17A0), the
 * loader object (0x4A1650 / 0x4A1690 / 0x4A1840) and the singleton (0x46EA50).  The macros and the scanner are
 * the ones of the other dat loaders. */
#include "game/common.h"
#include "game/inputcfg.h"
#include "game/gamefile.h"
#include "game/datlexer.h"
#include "game/fsarchive.h"
#include "game/globals.h"

ORIG_DATA(00610078); /* CReadInputCfg::vftable */
ORIG_DATA(00610070); /* CSingleton<CReadInputCfg>::vftable */
ORIG_DATA(00607BC8); /* the message of the failed singleton allocation */
ORIG_DATA(00607E98); /* "e:\prog\att1\singleton.h" */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006C9068); /* the text of the last token */

inline void *operator new(unsigned int, void *p) { return p; }

/* 0x4A1230 (the fill that reports the end position) already has its translation in src/fixed: it forwards the
 * allocator argument to the fill loop as the template's extra arguments.  The original passes the vector
 * itself in ECX there, so the callers below do the same. */
extern "C" CfgPair *__thiscall f_004A1230(unsigned allocator, CfgPair *dst, unsigned count,
                                          const CfgPair *value);

/* the size guard of the vector: count * 0x38 elements */
static const unsigned kMaxCfgPairs = 0x4924924u;

/* --- vector<CfgPair> elements ------------------------------------------------------------------------- */

/* The default constructor makes the two empty texts. */
DECOMP(004A0BA0)
CfgPair *__fastcall ConstructCfgPair(CfgPair *pair)
{
    new (pair) CfgPair;
    return pair;
}

/* The copy constructor copies the key, then the value. */
DECOMP(004A0C90)
CfgPair *__thiscall CopyConstructCfgPair(CfgPair *pair, const CfgPair *other)
{
    new (pair) CfgPair(*other);
    return pair;
}

/* The assignment copies both texts. */
DECOMP(004A0D10)
CfgPair *__thiscall AssignCfgPair(CfgPair *pair, const CfgPair *other)
{
    *pair = *other;
    return pair;
}

/* The destructor destroys the value first, then the key (the reverse of their construction). */
DECOMP(004A1130)
void __cdecl DestroyCfgPairs(CfgPair *first, CfgPair *last)
{
    for (; first != last; ++first)
        first->~CfgPair();
}

/* --- vector<CfgPair> storage -------------------------------------------------------------------------- */

DECOMP(004A0C30)
int __fastcall CfgPairCapacity(const CfgPairVector *vector)
{
    if (vector->begin == nullptr)
        return 0;
    return (unsigned)(vector->limit - vector->begin);
}

DECOMP(004A0C60)
int __fastcall CfgPairCount(const CfgPairVector *vector)
{
    if (vector->begin == nullptr)
        return 0;
    return (unsigned)(vector->end - vector->begin);
}

/* _Buy's block: count pairs through operator new; a huge count is the length_error of _Xlen. */
DECOMP(004A0E10)
CfgPair *__cdecl AllocateCfgPairs(unsigned count)
{
    if (count != 0 && 0xFFFFFFFFu / count < sizeof(CfgPair))
        ThrowVectorLengthError();
    return (CfgPair *)operator new(count * sizeof(CfgPair));
}

/* Copy-constructs [first, last) at dst and returns the position after them. */
DECOMP(004A0F80)
CfgPair *__cdecl CopyConstructCfgPairs(const CfgPair *first, const CfgPair *last, CfgPair *dst)
{
    for (; first != last; ++first, ++dst)
        new (dst) CfgPair(*first);
    return dst;
}

/* The copy that reports the end position (the wrapper the insertion algorithms use). */
DECOMP(004A1300)
CfgPair *__stdcall CopyConstructCfgPairsEnd(const CfgPair *first, const CfgPair *last, CfgPair *dst)
{
    return CopyConstructCfgPairs(first, last, dst);
}

/* Constructs count copies of value at dst. */
DECOMP(004A1080)
void __cdecl FillConstructCfgPairs(CfgPair *dst, unsigned count, const CfgPair *value)
{
    for (; count != 0; --count, ++dst)
        new (dst) CfgPair(*value);
}

/* Assigns copies of value over [first, last). */
DECOMP(004A0E80)
void __cdecl FillAssignCfgPairs(CfgPair *first, CfgPair *last, const CfgPair *value)
{
    for (; first != last; ++first)
        *first = *value;
}

/* std::copy_backward: the last pair is assigned first. */
DECOMP(004A0D40)
CfgPair *__cdecl CopyBackwardCfgPairs(CfgPair *first, CfgPair *last, CfgPair *dst)
{
    while (first != last) {
        --last;
        --dst;
        *dst = *last;
    }
    return dst;
}

/* vector::_Buy: the three pointers start empty, then count slots are allocated; the size guard first checks
 * the same limit as the allocation.  Returns false for an empty request. */
DECOMP(004A1020)
bool __thiscall BuyCfgPairs(CfgPairVector *vector, unsigned count)
{
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
    if (count == 0)
        return false;
    if (count > kMaxCfgPairs)
        ThrowVectorLengthError();
    CfgPair *data = AllocateCfgPairs(count);
    vector->begin = data;
    vector->end = data;
    vector->limit = data + count;
    return true;
}

/* vector's lifetime: the elements are destroyed, the block freed and the three pointers cleared; the
 * allocator dword stays as the owner left it. */
DECOMP(004A12C0)
void __fastcall DestroyCfgPairVector(CfgPairVector *vector)
{
    if (vector->begin != nullptr) {
        DestroyCfgPairs(vector->begin, vector->end);
        operator delete(vector->begin);
    }
    vector->begin = nullptr;
    vector->end = nullptr;
    vector->limit = nullptr;
}

/* vector::_Insert_n: count copies of value go in at position.  The value is copied to a stack temporary
 * first, because it may point into the vector the reallocation below frees.  A short capacity grows to half
 * again as much (or to the new size), moves the two ranges around the new pairs and frees the old block;
 * otherwise the tail either moves after the new pairs when it is shorter than count, or its last count
 * pairs move first into the grown raw tail and the middle shifts over the filled range. */
DECOMP(004A1330)
void __thiscall InsertCfgPairs(CfgPairVector *vector, CfgPair *position, unsigned count,
                               const CfgPair *value)
{
    CfgPair temporary(*value);
    if (count == 0)
        return;

    CfgPair *begin = vector->begin;
    CfgPair *end = vector->end;
    unsigned size = begin ? (unsigned)(end - begin) : 0;
    unsigned capacity = begin ? (unsigned)(vector->limit - begin) : 0;
    if (size > kMaxCfgPairs - count)
        ThrowVectorLengthError();

    if (capacity < size + count) {
        unsigned grown = capacity > kMaxCfgPairs - capacity / 2 ? 0 : capacity + capacity / 2;
        if (grown < size + count)
            grown = size + count;
        CfgPair *data = AllocateCfgPairs(grown);
        CfgPair *dst = CopyConstructCfgPairs(begin, position, data);
        dst = f_004A1230((unsigned)vector, dst, count, &temporary);
        CopyConstructCfgPairs(position, end, dst);
        if (begin != nullptr) {
            DestroyCfgPairs(begin, end);
            operator delete(begin);
        }
        vector->limit = data + grown;
        vector->end = data + size + count;
        vector->begin = data;
        return;
    }

    unsigned tail = (unsigned)(end - position);
    if (tail < count) {
        CopyConstructCfgPairsEnd(position, end, position + count);
        f_004A1230((unsigned)vector, end, count - tail, &temporary);
        vector->end = end + count;
        FillAssignCfgPairs(position, end, &temporary);
        return;
    }

    CopyConstructCfgPairsEnd(end - count, end, end);
    vector->end = end + count;
    CopyBackwardCfgPairs(position, end - count, end);
    FillAssignCfgPairs(position, position + count, &temporary);
}

/* vector::insert(position, 1, value) as the push path calls it: the returned iterator is the new element. */
DECOMP(004A1710)
void __thiscall InsertCfgPairAt(CfgPairVector *vector, CfgPair **result, CfgPair *position,
                                const CfgPair *value)
{
    CfgPair *begin = vector->begin;
    unsigned index = 0;
    if (begin != nullptr && vector->end != begin)
        index = (unsigned)(position - begin);
    InsertCfgPairs(vector, position, 1, value);
    *result = vector->begin + index;
}

/* vector::push_back: a spare slot constructs the pair in place, otherwise the insertion above runs with the
 * end as the position. */
DECOMP(004A17A0)
void __thiscall PushCfgPair(CfgPairVector *vector, const CfgPair *value)
{
    CfgPair *begin = vector->begin;
    if (begin != nullptr && (unsigned)(vector->end - begin) < (unsigned)(vector->limit - begin)) {
        FillConstructCfgPairs(vector->end, 1, value);
        vector->end += 1;
        return;
    }
    CfgPair *result;
    InsertCfgPairAt(vector, &result, vector->end, value);
}

/* --- the loader object -------------------------------------------------------------------------------- */

/* The loader's constructor: the class vtable and an empty vector.  The original leaves EDX alone (the symbol
 * table says only EAX and ECX change), so it is saved around the stores. */
DECOMP(004A1650)
CReadInputCfg::CReadInputCfg()
{
    unsigned savedEdx;
    __asm__ __volatile__("movl %%edx, %0" : "=m"(savedEdx));
    vftable = d_00610078;
    entries.begin = nullptr;
    entries.end = nullptr;
    entries.limit = nullptr;
    __asm__ __volatile__("movl %0, %%edx" : : "m"(savedEdx));
}

/* The loader's destructor: the class vtable, the pairs freed and the vector cleared, then the singleton
 * vtable of the base. */
DECOMP(004A1690)
CReadInputCfg::~CReadInputCfg()
{
    vftable = d_00610078;
    if (entries.begin != nullptr) {
        DestroyCfgPairs(entries.begin, entries.end);
        operator delete(entries.begin);
    }
    entries.begin = nullptr;
    entries.end = nullptr;
    entries.limit = nullptr;
    vftable = d_00610070;
}

/* The deleting destructor of the class vtable: the object is destroyed and, for bit 0 of the flags, freed. */
DECOMP(004A1780)
CReadInputCfg *__thiscall DeleteCReadInputCfg(CReadInputCfg *object, unsigned char flags)
{
    object->~CReadInputCfg();
    if ((flags & 1) != 0)
        operator delete(object);
    return object;
}

/* The singleton: the first call allocates and constructs the loader; a failed allocation throws the
 * singleton's exception. */
DECOMP(0046EA50)
CReadInputCfg *__stdcall CReadInputCfg::Instance()
{
    if (!g_inputCfgInstance) {
        void *memory = operator new(sizeof(CReadInputCfg));
        g_inputCfgInstance = memory ? new (memory) CReadInputCfg() : nullptr;
        if (!g_inputCfgInstance)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607E98), 16);
    }
    return g_inputCfgInstance;
}

/* Opens input.cfg through the shared CGameFile, remembers the file size for the lexer, and pushes a pair for
 * every two tokens until the end of the file. */
DECOMP(004A1840)
void CReadInputCfg::Load(const std::string &name)
{
    CGameFile *reader = (CGameFile *)d_006CA280;
    reader->Open(name, 1);
    ORIG_VAR(006CA278, unsigned) = reader->file->size;

    CfgPair pair;
    for (int token = DatLexerNextToken(); token != 0; token = DatLexerNextToken()) {
        pair.key = (const char *)d_006C9068;
        DatLexerNextToken();
        pair.value = (const char *)d_006C9068;
        PushCfgPair(&entries, &pair);
    }
    reader->Close();
}
