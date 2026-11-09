/* CReadInterfaceDat: the interface record table and its lifetime (0x4A7160 / 0x4A70C0) and its loader (0x4A71E0),
 * with the InterfaceRecord parser and lifetime (0x4A6610 / 0x4A6D30 / 0x4A6E90 / 0x4A6740). */
#include "game/common.h"
#include "game/interfacedat.h"
#include "game/gamefile.h"
#include "game/datlexer.h"

ORIG_DATA(00610088); /* CReadInterfaceDat::vftable */
ORIG_DATA(00610080); /* CSingleton<CReadInterfaceDat>::vftable */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006CA2BC); /* the token the lexer returned last */
ORIG_DATA(006C9060); /* the numeric value of the last token (a float) */
ORIG_DATA(006C9068); /* the text of the last token */

inline void *operator new(unsigned int, void *p) { return p; }

ORIG_THISCALL(004EF350, void, (void *vector, unsigned count, void *sentinel)); /* refill the bucket vector */
ORIG_THISCALL(00424270, void *, (void *map, const void *key));         /* find the record's node, or insert one */

/* the keyword parsers of the record fields (they read through the same lexer and leave the token global advanced) */
ORIG_FASTCALL(004A1CA0, void, (float *floats));    /* 0x149: x, y and optionally x2, y2 */

extern "C" __declspec(dllimport) char *__cdecl _strlwr(char *s); /* 0x607414 */

/* vector assignment of the element types (std::vector::operator= of the game's own classes) */
ORIG_THISCALL(004A5360, void *, (void *vector, const void *other)); /* 0x4C-byte elements */
ORIG_THISCALL(004A5580, void *, (void *vector, const void *other)); /* 0x48-byte elements */
ORIG_THISCALL(004A57A0, void *, (void *vector, const void *other)); /* 0x2C-byte elements */
ORIG_THISCALL(004A69E0, void *, (void *vector, const void *other)); /* 0x64-byte elements */
ORIG_THISCALL(004A5A10, void *, (void *vector, const void *other)); /* 0xE4-byte elements */
ORIG_THISCALL(004A5C50, void *, (void *vector, const void *other)); /* 0x118-byte elements */

/* The element copy the vectors make: the strings copy themselves, the numbers follow one by one. The flag is a
 * lone byte, so the three padding bytes after it keep whatever the destination held. */
DECOMP(00421020)
InterfaceItem4C::InterfaceItem4C(const InterfaceItem4C &other)
    : name(other.name), text(other.text), flag(other.flag), x(other.x), y(other.y), x2(other.x2), y2(other.y2)
{
}

/* An item keeps some of its strings 0x20 apart; the compiler-generated destructors release the later one first.
 * 0x420910 is that pair destructor: the string at +0x2C, then the one at +0x0C. */
DECOMP(00420910)
void __fastcall DestroyStringPair(char *pair)
{
    ((std::string *)(pair + 0x2C))->~basic_string();
    ((std::string *)(pair + 0x0C))->~basic_string();
}

/* The two largest elements destroy their strings from the last one back, in the order the original does: the
 * pairs go through 0x420910, the lone strings directly. */
DECOMP(00420F10)
InterfaceItemE4::~InterfaceItemE4()
{
    text6.~basic_string();
    text5.~basic_string();
    DestroyStringPair((char *)this + 0x64); /* text4 and text3 */
    DestroyStringPair((char *)this + 0x1C); /* text2 and text1 */
    name.~basic_string();
}

DECOMP(00420F90)
InterfaceItem118::~InterfaceItem118()
{
    DestroyStringPair((char *)this + 0xD0); /* text7 and text6 */
    text5.~basic_string();
    DestroyStringPair((char *)this + 0x68); /* text4 and text3 */
    DestroyStringPair((char *)this + 0x1C); /* text2 and text1 */
    name.~basic_string();
}

/* The range destroyers the clears and assignments use: every element releases its strings, latest first. */
DECOMP(00422B90)
void DestroyItems4C(InterfaceItem4C *first, InterfaceItem4C *last)
{
    for (; first != last; first++) {
        first->text.~basic_string();
        first->name.~basic_string();
    }
}

DECOMP(00422BF0)
void DestroyItems48(InterfaceItem48 *first, InterfaceItem48 *last)
{
    for (; first != last; first++) {
        first->text.~basic_string();
        first->name.~basic_string();
    }
}

DECOMP(00422C50)
void DestroyItems64(InterfaceItem64 *first, InterfaceItem64 *last)
{
    for (; first != last; first++) {
        first->text2.~basic_string();
        first->text1.~basic_string();
        first->name.~basic_string();
    }
}

/* The vector destructors: the elements go, then their buffer, and the three pointers are zeroed. */
DECOMP(00497C10)
void __fastcall DestroyVector2C(InterfaceVector *vector)
{
    InterfaceItem2C *first = (InterfaceItem2C *)vector->begin;
    if (first) {
        InterfaceItem2C *last = (InterfaceItem2C *)vector->end;
        for (; first != last; first++)
            first->name.~basic_string();
        operator delete[](vector->begin);
    }
    vector->begin = vector->end = vector->limit = nullptr;
}

DECOMP(00423210)
void __fastcall DestroyVectorE4(InterfaceVector *vector)
{
    InterfaceItemE4 *first = (InterfaceItemE4 *)vector->begin;
    if (first) {
        InterfaceItemE4 *last = (InterfaceItemE4 *)vector->end;
        for (; first != last; first++)
            first->~InterfaceItemE4();
        operator delete[](vector->begin);
    }
    vector->begin = vector->end = vector->limit = nullptr;
}

DECOMP(00423260)
void __fastcall DestroyVector118(InterfaceVector *vector)
{
    InterfaceItem118 *first = (InterfaceItem118 *)vector->begin;
    if (first) {
        InterfaceItem118 *last = (InterfaceItem118 *)vector->end;
        for (; first != last; first++)
            first->~InterfaceItem118();
        operator delete[](vector->begin);
    }
    vector->begin = vector->end = vector->limit = nullptr;
}

/* The clears: the elements go and the end drops to the begin, but the buffer stays allocated. */
DECOMP(004A4C00)
void __fastcall ClearVector4C(InterfaceVector *vector)
{
    InterfaceItem4C *first = (InterfaceItem4C *)vector->begin;
    InterfaceItem4C *last = (InterfaceItem4C *)vector->end;
    if (first != last) {
        DestroyItems4C(first, last);
        vector->end = first;
    }
}

DECOMP(004A4C50)
void __fastcall ClearVector48(InterfaceVector *vector)
{
    InterfaceItem48 *first = (InterfaceItem48 *)vector->begin;
    InterfaceItem48 *last = (InterfaceItem48 *)vector->end;
    if (first != last) {
        DestroyItems48(first, last);
        vector->end = first;
    }
}

/* The titled collections clear the same way: the title empties first, then the elements go. */
DECOMP(004A5270)
void __fastcall ClearCollection4C(InterfaceCollection *collection)
{
    collection->title = "";
    InterfaceItem4C *first = (InterfaceItem4C *)collection->begin;
    InterfaceItem4C *last = (InterfaceItem4C *)collection->end;
    if (first != last) {
        DestroyItems4C(first, last);
        collection->end = first;
    }
}

DECOMP(004A52D0)
void __fastcall ClearCollection48(InterfaceCollection *collection)
{
    collection->title = "";
    InterfaceItem48 *first = (InterfaceItem48 *)collection->begin;
    InterfaceItem48 *last = (InterfaceItem48 *)collection->end;
    if (first != last) {
        DestroyItems48(first, last);
        collection->end = first;
    }
}

/* The record starts empty: all vectors are null and the named strings are empty. The vectors' allocator bytes stay
 * uninitialised, as in the original. */
DECOMP(004A6610)
InterfaceRecord::InterfaceRecord()
{
    name = "";
    number14B = 0;
    text147 = "";

    items143.begin = items143.end = items143.limit = nullptr;
    items144.begin = items144.end = items144.limit = nullptr;
    items145.begin = items145.end = items145.limit = nullptr;
    items146.begin = items146.end = items146.limit = nullptr;
    items14A.begin = items14A.end = items14A.limit = nullptr;
    items14C.begin = items14C.end = items14C.limit = nullptr;
}

/* The vectors free their elements and buffers here; the strings (name, texts and the collection titles) are
 * destroyed by the compiler-generated tail. */
DECOMP(004A6740)
InterfaceRecord::~InterfaceRecord()
{
    text142[0] = "";
    text142[1] = "";

    ClearCollection4C(&items143);
    if (items143.begin) {
        operator delete[](items143.begin);
        items143.begin = items143.end = items143.limit = nullptr;
    }

    ClearCollection48(&items144);
    if (items144.begin) {
        operator delete[](items144.begin);
        items144.begin = items144.end = items144.limit = nullptr;
    }

    items145.title = "";
    DestroyVector2C((InterfaceVector *)&items145.allocator);

    if (items146.begin) {
        DestroyItems64((InterfaceItem64 *)items146.begin, (InterfaceItem64 *)items146.end);
        operator delete[](items146.begin);
        items146.begin = items146.end = items146.limit = nullptr;
    }

    DestroyVectorE4(&items14A);
    DestroyVector118(&items14C);
}

DECOMP(004A6E90)
InterfaceRecord &InterfaceRecord::operator=(const InterfaceRecord &other)
{
    name = other.name;
    text142[0] = other.text142[0];
    text142[1] = other.text142[1];

    items143.title = other.items143.title;
    sub_004A5360(&items143.allocator, &other.items143.allocator);

    items144.title = other.items144.title;
    sub_004A5580(&items144.allocator, &other.items144.allocator);

    items145.title = other.items145.title;
    sub_004A57A0(&items145.allocator, &other.items145.allocator);

    sub_004A69E0(&items146, &other.items146);

    text147 = other.text147;
    number14B = other.number14B;
    for (int i = 0; i < 4; i++)
        floats149[i] = other.floats149[i];

    sub_004A5A10(&items14A, &other.items14A);
    sub_004A5C50(&items14C, &other.items14C);
    return *this;
}

/* An element line: the name token is already the current one, the parser reads the rest itself and leaves the
 * token global on the next line's first token. Numbers after a 0x105 token are the optional x2/y2 pair. */
DECOMP(004A1A60)
void InterfaceItem4C::Read()
{
    name = _strlwr(d_006C9068);
    DatLexerNextToken();
    text = (const char *)d_006C9068;
    DatLexerNextToken();
    flag = (unsigned char)(int)ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    x = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    y = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        x2 = 0;
        y2 = 0;
        return;
    }
    x2 = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    y2 = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
}

DECOMP(004A1B10)
void InterfaceItem48::Read()
{
    name = _strlwr(d_006C9068);
    DatLexerNextToken();
    text = (const char *)d_006C9068;
    DatLexerNextToken();
    x = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    y = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        x2 = 0;
        y2 = 0;
        return;
    }
    x2 = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    y2 = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
}

/* The vector append of the interface element types (std::vector<T>::push_back): one copy of the item at the end.
 * The item is copied before the vector is touched, an empty or full vector grows to half again (at least one
 * more element), the elements move to the new buffer and the old buffer goes; the element copies are the
 * compiler's (the string copy constructor is the same import the original's copy constructors call). */
template <typename T>
static void PushBack(InterfaceVector *vector, const T *item)
{
    T *begin = (T *)vector->begin;
    T *end = (T *)vector->end;
    unsigned size = begin ? (unsigned)(end - begin) : 0;
    unsigned capacity = begin ? (unsigned)((T *)vector->limit - begin) : 0;

    if (begin && size < capacity) {
        ::new (end) T(*item);
        vector->end = end + 1;
        return;
    }

    T copy(*item);
    unsigned grown = capacity + capacity / 2;
    if (grown < size + 1)
        grown = size + 1;
    T *data = (T *)operator new(grown * sizeof(T));
    unsigned i = 0;
    for (; i < size; i++)
        ::new (data + i) T(begin[i]);
    ::new (data + size) T(copy);
    if (begin) {
        for (T *p = begin; p != end; p++)
            p->~T();
        operator delete(begin);
    }
    vector->begin = data;
    vector->end = data + size + 1;
    vector->limit = data + grown;
}

DECOMP(004A54F0)
void __thiscall PushItem4C(InterfaceVector *vector, const InterfaceItem4C *item)
{
    PushBack(vector, item);
}

DECOMP(004A5710)
void __thiscall PushItem48(InterfaceVector *vector, const InterfaceItem48 *item)
{
    PushBack(vector, item);
}

DECOMP(004A5930)
void __thiscall PushItem2C(InterfaceVector *vector, const InterfaceItem2C *item)
{
    PushBack(vector, item);
}

DECOMP(004A6B70)
void __thiscall PushItem64(InterfaceVector *vector, const InterfaceItem64 *item)
{
    PushBack(vector, item);
}

DECOMP(004A5BB0)
void __thiscall PushItemE4(InterfaceVector *vector, const InterfaceItemE4 *item)
{
    PushBack(vector, item);
}

DECOMP(004A5DF0)
void __thiscall PushItem118(InterfaceVector *vector, const InterfaceItem118 *item)
{
    PushBack(vector, item);
}

/* A titled block: "title { lines }"; the opening brace is read and dropped, the block ends on token 0x103. */
DECOMP(004A5F00)
void InterfaceCollection::ReadItems4C()
{
    DatLexerNextToken();
    title = (const char *)d_006C9068;
    DatLexerNextToken();

    InterfaceItem4C item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.Read();
        PushItem4C((InterfaceVector *)&allocator, &item);
    }
}

DECOMP(004A5FD0)
void InterfaceCollection::ReadItems48()
{
    DatLexerNextToken();
    title = (const char *)d_006C9068;
    DatLexerNextToken();

    InterfaceItem48 item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.Read();
        PushItem48((InterfaceVector *)&allocator, &item);
    }
}

DECOMP(004A60A0)
void InterfaceCollection::ReadItems2C()
{
    DatLexerNextToken();
    title = (const char *)d_006C9068;
    DatLexerNextToken();

    InterfaceItem2C item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        DatLexerNextToken();
        item.x = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.y = ORIG_VAR(006C9060, float);

        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
        if (ORIG_VAR(006CA2BC, int) == 0x105) {
            item.x2 = ORIG_VAR(006C9060, float);
            DatLexerNextToken();
            item.y2 = ORIG_VAR(006C9060, float);
            ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
        } else {
            item.x2 = 0;
            item.y2 = 0;
        }
        PushItem2C((InterfaceVector *)&allocator, &item);
    }
}

DECOMP(004A6C00)
void InterfaceVector::ReadItems64()
{
    DatLexerNextToken();

    InterfaceItem64 item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        DatLexerNextToken();
        item.x = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.y = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag = d_006C9068[0];
        DatLexerNextToken();
        item.text1 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.z = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text2 = (const char *)d_006C9068;

        PushItem64(this, &item);
        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    }
}

/* The 0x14A lines keep the name twice: the raw token and, at +0xC8, the token without its last character,
 * lowercased. */
DECOMP(004A61C0)
void InterfaceVector::ReadItemsE4()
{
    DatLexerNextToken();

    InterfaceItemE4 item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        d_006C9068[strlen(d_006C9068) - 1] = '\0';
        _strlwr(d_006C9068);
        item.text6 = (const char *)d_006C9068;

        DatLexerNextToken();
        item.x = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.y = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag = d_006C9068[0];
        DatLexerNextToken();
        item.text1 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.z = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text2 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.u = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.v = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag2 = d_006C9068[0];
        DatLexerNextToken();
        item.text3 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.w = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text4 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.text5 = (const char *)d_006C9068;

        PushItemE4(this, &item);
        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    }
}

DECOMP(004A63B0)
void InterfaceVector::ReadItems118()
{
    DatLexerNextToken();

    InterfaceItem118 item;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        DatLexerNextToken();
        item.x = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.y = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag = d_006C9068[0];
        DatLexerNextToken();
        item.text1 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.z = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text2 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.u = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.v = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.w = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag2 = d_006C9068[0];
        DatLexerNextToken();
        item.text3 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.a = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text4 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.b = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text5 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.c = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.d = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.flag3 = d_006C9068[0];
        DatLexerNextToken();
        item.text6 = (const char *)d_006C9068;
        DatLexerNextToken();
        item.e = ORIG_VAR(006C9060, float);
        DatLexerNextToken();
        item.text7 = (const char *)d_006C9068;

        PushItem118(this, &item);
        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    }
}

DECOMP(004A1CA0)
void __fastcall ReadFloats149(float *floats)
{
    DatLexerNextToken();
    floats[0] = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    floats[1] = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        floats[2] = 0;
        floats[3] = 0;
        return;
    }
    floats[2] = ORIG_VAR(006C9060, float);
    DatLexerNextToken();
    floats[3] = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
}

/* The record's keywords up to the closing token 0x103. A keyword parser consumes its whole line, so the token
 * global already holds the next keyword; 0x149 advances it itself, so it goes straight back to the check. */
DECOMP(004A6D30)
void InterfaceRecord::Read()
{
    DatLexerNextToken();
    name = (const char *)d_006C9068;
    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();

    for (;;) {
        if (ORIG_VAR(006CA2BC, int) == 0x103)
            return;

        switch (ORIG_VAR(006CA2BC, int)) {
        case 0x142:
            DatLexerNextToken();
            text142[0] = (const char *)d_006C9068;
            DatLexerNextToken();
            text142[1] = (const char *)d_006C9068;
            break;
        case 0x143:
            items143.ReadItems4C();
            break;
        case 0x144:
            items144.ReadItems48();
            break;
        case 0x145:
            items145.ReadItems2C();
            break;
        case 0x146:
            items146.ReadItems64();
            break;
        case 0x147:
            DatLexerNextToken();
            text147 = (const char *)d_006C9068;
            break;
        case 0x149:
            ReadFloats149(floats149);
            continue;
        case 0x14A:
            items14A.ReadItemsE4();
            break;
        case 0x14B:
            DatLexerNextToken();
            number14B = ORIG_VAR(006C9060, float);
            break;
        case 0x14C:
            items14C.ReadItems118();
            break;
        }

        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    }
}

/* The record map's sentinel: a bare 0x15C-byte node linking to itself.  Like the map's other sentinels it
 * never carries a key or a value, so neither is constructed. */
DECOMP(004A2B40)
InterfaceRecordNode *__stdcall CreateRecordNodeSentinel()
{
    InterfaceRecordNode *node = (InterfaceRecordNode *)operator new(sizeof(InterfaceRecordNode));
    node->next = node;
    node->prev = node;
    return node;
}

/* The record map's constructor: the allocator byte from the caller, the node sentinel, a zero size and the
 * nine initial buckets all pointing at the sentinel.  Like the generic map ctors it returns the map in EAX. */
DECOMP(004A7040)
FsHashMap *__thiscall InitRecordMap(FsHashMap *map, const unsigned char *allocator, const void *compare)
{
    *(unsigned char *)map = *allocator;
    map->sentinel = CreateRecordNodeSentinel();
    map->size = 0;
    void *sentinel = map->sentinel;
    InitPointerVector(&map->vectorAlloc, 9, &sentinel);
    map->mask = 1;
    map->count = 1;
    return map;
}

/* Empties the record map: every node's record and key are destroyed and the node freed.  The library's view
 * of the map begins at FsHashMap+4, so the head sentinel is the map's field at +8 and the size the field at
 * +0xC.  This is ClearStringNodeList's twin for the record-valued nodes (the record sits at +0x24). */
DECOMP(00422AD0)
void __fastcall ClearRecordNodeList(char *mapObject)
{
    InterfaceRecordNode *head = *(InterfaceRecordNode **)(mapObject + 4);
    InterfaceRecordNode *node = head->next;
    head->next = head;
    head->prev = head;
    *(unsigned *)(mapObject + 8) = 0;
    while (node != head) {
        InterfaceRecordNode *next = node->next;
        node->value.~InterfaceRecord();
        node->key.~basic_string();
        operator delete(node);
        node = next;
    }
}

/* the original hands the map ctor an uninitialised stack byte for the empty allocator; nothing reads it */
DECOMP(004A7160)
CReadInterfaceDat::CReadInterfaceDat()
{
    char allocator = 0;
    vftable = d_00610088;
    InitRecordMap(&map, (const unsigned char *)&allocator, &allocator);
}

DECOMP(004A70C0)
CReadInterfaceDat::~CReadInterfaceDat()
{
    vftable = d_00610088;

    if (map.begin)
        operator delete(map.begin);
    map.begin = nullptr;
    map.end = nullptr;
    map.limit = nullptr;

    /* the tree part at map+4 destroys the keys and the records and frees the nodes */
    ClearRecordNodeList((char *)&map + 4);
    operator delete(map.sentinel);
    map.sentinel = nullptr;

    vftable = d_00610080;
}

/* The loaders share one CGameFile (it reads the whole file into memory), then the lexer (0x470410) walks it token
 * by token: a token 0x141 starts a record whose keywords follow up to token 0x103, and the map is keyed by the
 * record's name (its first string). */
DECOMP(004A71E0)
void CReadInterfaceDat::Load(const std::string &name)
{
    CGameFile *reader = (CGameFile *)d_006CA280;
    reader->Open(name, 1);
    ORIG_VAR(006CA278, unsigned) = reader->file->size;

    ClearRecordNodeList((char *)&map + 4);
    void *sentinel = map.sentinel;
    sub_004EF350(&map.vectorAlloc, 9, &sentinel);
    map.mask = 1;
    map.count = 1;

    ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2BC, int) != 0) {
        if (ORIG_VAR(006CA2BC, int) == 0x141) {
            InterfaceRecord record;
            record.Read();
            *(InterfaceRecord *)sub_00424270(&map, &record) = record;
        }
        ORIG_VAR(006CA2BC, int) = DatLexerNextToken();
    }
    reader->Close();
}
