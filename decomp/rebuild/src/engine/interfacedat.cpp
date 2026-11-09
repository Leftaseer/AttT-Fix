/* CReadInterfaceDat: the interface record table and its lifetime (0x4A7160 / 0x4A70C0) and its loader (0x4A71E0),
 * with the InterfaceRecord parser and lifetime (0x4A6610 / 0x4A6D30 / 0x4A6E90 / 0x4A6740). */
#include "game/common.h"
#include "game/interfacedat.h"
#include "game/gamefile.h"

ORIG_DATA(00610088); /* CReadInterfaceDat::vftable */
ORIG_DATA(00610080); /* CSingleton<CReadInterfaceDat>::vftable */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006CA2BC); /* the token the lexer returned last */
ORIG_DATA(006C9060); /* the numeric value of the last token (a float) */
ORIG_DATA(006C9068); /* the text of the last token */

ORIG_THISCALL(004EF350, void, (void *vector, unsigned count, void *sentinel)); /* refill the bucket vector */
ORIG_FN(00470410, int, ());                                            /* the next token of the file */
ORIG_THISCALL(00424270, void *, (void *map, const void *key));         /* find the record's node, or insert one */

/* the keyword parsers of the record fields (they read through the same lexer and leave the token global advanced) */
ORIG_FASTCALL(004A1CA0, void, (float *floats));    /* 0x149: x, y and optionally x2, y2 */

/* the vector append of each element type */
ORIG_THISCALL(004A54F0, void, (void *vector, const void *item)); /* 0x4C-byte elements */
ORIG_THISCALL(004A5710, void, (void *vector, const void *item)); /* 0x48-byte elements */
ORIG_THISCALL(004A5930, void, (void *vector, const void *item)); /* 0x2C-byte elements */
ORIG_THISCALL(004A6B70, void, (void *vector, const void *item)); /* 0x64-byte elements */
ORIG_THISCALL(004A5BB0, void, (void *vector, const void *item)); /* 0xE4-byte elements */
ORIG_THISCALL(004A5DF0, void, (void *vector, const void *item)); /* 0x118-byte elements */

extern "C" __declspec(dllimport) char *__cdecl _strlwr(char *s); /* 0x607414 */

/* vector assignment of the element types (std::vector::operator= of the game's own classes) */
ORIG_THISCALL(004A5360, void *, (void *vector, const void *other)); /* 0x4C-byte elements */
ORIG_THISCALL(004A5580, void *, (void *vector, const void *other)); /* 0x48-byte elements */
ORIG_THISCALL(004A57A0, void *, (void *vector, const void *other)); /* 0x2C-byte elements */
ORIG_THISCALL(004A69E0, void *, (void *vector, const void *other)); /* 0x64-byte elements */
ORIG_THISCALL(004A5A10, void *, (void *vector, const void *other)); /* 0xE4-byte elements */
ORIG_THISCALL(004A5C50, void *, (void *vector, const void *other)); /* 0x118-byte elements */

/* the element range destructors / container clears the record destructor uses */
ORIG_FASTCALL(004A5270, void, (void *collection));               /* clear: title = "" and destroy 0x4C elements */
ORIG_FASTCALL(004A52D0, void, (void *collection));               /* clear: title = "" and destroy 0x48 elements */
ORIG_FASTCALL(00497C10, void, (void *vector));                   /* destroy 0x2C elements and free the buffer */
ORIG_FN(00422C50, void, (void *first, void *last));              /* destroy 0x64 elements */
ORIG_FASTCALL(00423210, void, (void *vector));                   /* destroy 0xE4 elements and free the buffer */
ORIG_FASTCALL(00423260, void, (void *vector));                   /* destroy 0x118 elements and free the buffer */

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

    sub_004A5270(&items143);
    if (items143.begin) {
        operator delete[](items143.begin);
        items143.begin = items143.end = items143.limit = nullptr;
    }

    sub_004A52D0(&items144);
    if (items144.begin) {
        operator delete[](items144.begin);
        items144.begin = items144.end = items144.limit = nullptr;
    }

    items145.title = "";
    sub_00497C10(&items145.allocator);

    if (items146.begin) {
        sub_00422C50(items146.begin, items146.end);
        operator delete[](items146.begin);
        items146.begin = items146.end = items146.limit = nullptr;
    }

    sub_00423210(&items14A);
    sub_00423260(&items14C);
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
    sub_00470410();
    text = (const char *)d_006C9068;
    sub_00470410();
    flag = (unsigned char)(int)ORIG_VAR(006C9060, float);
    sub_00470410();
    x = ORIG_VAR(006C9060, float);
    sub_00470410();
    y = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = sub_00470410();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        x2 = 0;
        y2 = 0;
        return;
    }
    x2 = ORIG_VAR(006C9060, float);
    sub_00470410();
    y2 = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = sub_00470410();
}

DECOMP(004A1B10)
void InterfaceItem48::Read()
{
    name = _strlwr(d_006C9068);
    sub_00470410();
    text = (const char *)d_006C9068;
    sub_00470410();
    x = ORIG_VAR(006C9060, float);
    sub_00470410();
    y = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = sub_00470410();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        x2 = 0;
        y2 = 0;
        return;
    }
    x2 = ORIG_VAR(006C9060, float);
    sub_00470410();
    y2 = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = sub_00470410();
}

/* A titled block: "title { lines }"; the opening brace is read and dropped, the block ends on token 0x103. */
DECOMP(004A5F00)
void InterfaceCollection::ReadItems4C()
{
    sub_00470410();
    title = (const char *)d_006C9068;
    sub_00470410();

    InterfaceItem4C item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.Read();
        sub_004A54F0(&allocator, &item);
    }
}

DECOMP(004A5FD0)
void InterfaceCollection::ReadItems48()
{
    sub_00470410();
    title = (const char *)d_006C9068;
    sub_00470410();

    InterfaceItem48 item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.Read();
        sub_004A5710(&allocator, &item);
    }
}

DECOMP(004A60A0)
void InterfaceCollection::ReadItems2C()
{
    sub_00470410();
    title = (const char *)d_006C9068;
    sub_00470410();

    InterfaceItem2C item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        sub_00470410();
        item.x = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.y = ORIG_VAR(006C9060, float);

        ORIG_VAR(006CA2BC, int) = sub_00470410();
        if (ORIG_VAR(006CA2BC, int) == 0x105) {
            item.x2 = ORIG_VAR(006C9060, float);
            sub_00470410();
            item.y2 = ORIG_VAR(006C9060, float);
            ORIG_VAR(006CA2BC, int) = sub_00470410();
        } else {
            item.x2 = 0;
            item.y2 = 0;
        }
        sub_004A5930(&allocator, &item);
    }
}

DECOMP(004A6C00)
void InterfaceVector::ReadItems64()
{
    sub_00470410();

    InterfaceItem64 item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        sub_00470410();
        item.x = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.y = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag = d_006C9068[0];
        sub_00470410();
        item.text1 = (const char *)d_006C9068;
        sub_00470410();
        item.z = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text2 = (const char *)d_006C9068;

        sub_004A6B70(this, &item);
        ORIG_VAR(006CA2BC, int) = sub_00470410();
    }
}

/* The 0x14A lines keep the name twice: the raw token and, at +0xC8, the token without its last character,
 * lowercased. */
DECOMP(004A61C0)
void InterfaceVector::ReadItemsE4()
{
    sub_00470410();

    InterfaceItemE4 item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        d_006C9068[strlen(d_006C9068) - 1] = '\0';
        _strlwr(d_006C9068);
        item.text6 = (const char *)d_006C9068;

        sub_00470410();
        item.x = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.y = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag = d_006C9068[0];
        sub_00470410();
        item.text1 = (const char *)d_006C9068;
        sub_00470410();
        item.z = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text2 = (const char *)d_006C9068;
        sub_00470410();
        item.u = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.v = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag2 = d_006C9068[0];
        sub_00470410();
        item.text3 = (const char *)d_006C9068;
        sub_00470410();
        item.w = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text4 = (const char *)d_006C9068;
        sub_00470410();
        item.text5 = (const char *)d_006C9068;

        sub_004A5BB0(this, &item);
        ORIG_VAR(006CA2BC, int) = sub_00470410();
    }
}

DECOMP(004A63B0)
void InterfaceVector::ReadItems118()
{
    sub_00470410();

    InterfaceItem118 item;
    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0x103) {
        item.name = (const char *)d_006C9068;
        sub_00470410();
        item.x = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.y = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag = d_006C9068[0];
        sub_00470410();
        item.text1 = (const char *)d_006C9068;
        sub_00470410();
        item.z = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text2 = (const char *)d_006C9068;
        sub_00470410();
        item.u = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.v = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.w = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag2 = d_006C9068[0];
        sub_00470410();
        item.text3 = (const char *)d_006C9068;
        sub_00470410();
        item.a = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text4 = (const char *)d_006C9068;
        sub_00470410();
        item.b = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text5 = (const char *)d_006C9068;
        sub_00470410();
        item.c = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.d = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.flag3 = d_006C9068[0];
        sub_00470410();
        item.text6 = (const char *)d_006C9068;
        sub_00470410();
        item.e = ORIG_VAR(006C9060, float);
        sub_00470410();
        item.text7 = (const char *)d_006C9068;

        sub_004A5DF0(this, &item);
        ORIG_VAR(006CA2BC, int) = sub_00470410();
    }
}

DECOMP(004A1CA0)
void __fastcall ReadFloats149(float *floats)
{
    sub_00470410();
    floats[0] = ORIG_VAR(006C9060, float);
    sub_00470410();
    floats[1] = ORIG_VAR(006C9060, float);

    ORIG_VAR(006CA2BC, int) = sub_00470410();
    if (ORIG_VAR(006CA2BC, int) != 0x105) {
        floats[2] = 0;
        floats[3] = 0;
        return;
    }
    floats[2] = ORIG_VAR(006C9060, float);
    sub_00470410();
    floats[3] = ORIG_VAR(006C9060, float);
    ORIG_VAR(006CA2BC, int) = sub_00470410();
}

/* The record's keywords up to the closing token 0x103. A keyword parser consumes its whole line, so the token
 * global already holds the next keyword; 0x149 advances it itself, so it goes straight back to the check. */
DECOMP(004A6D30)
void InterfaceRecord::Read()
{
    sub_00470410();
    name = (const char *)d_006C9068;
    ORIG_VAR(006CA2BC, int) = sub_00470410();

    for (;;) {
        if (ORIG_VAR(006CA2BC, int) == 0x103)
            return;

        switch (ORIG_VAR(006CA2BC, int)) {
        case 0x142:
            sub_00470410();
            text142[0] = (const char *)d_006C9068;
            sub_00470410();
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
            sub_00470410();
            text147 = (const char *)d_006C9068;
            break;
        case 0x149:
            ReadFloats149(floats149);
            continue;
        case 0x14A:
            items14A.ReadItemsE4();
            break;
        case 0x14B:
            sub_00470410();
            number14B = ORIG_VAR(006C9060, float);
            break;
        case 0x14C:
            items14C.ReadItems118();
            break;
        }

        ORIG_VAR(006CA2BC, int) = sub_00470410();
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

    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0) {
        if (ORIG_VAR(006CA2BC, int) == 0x141) {
            InterfaceRecord record;
            record.Read();
            *(InterfaceRecord *)sub_00424270(&map, &record) = record;
        }
        ORIG_VAR(006CA2BC, int) = sub_00470410();
    }
    reader->Close();
}
