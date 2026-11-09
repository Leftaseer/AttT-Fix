/* CReadCursorDat: the cursor map of Cursors.dat and its lifetime (0x4A0910 / 0x4A0870) and its loader (0x4A0990),
 * with the map's node helpers (0x442CE0 / 0x442EC0 / 0x442FF0 / 0x4430D0 / 0x443520 / 0x4437E0). */
#include "game/common.h"
#include "game/cursordat.h"
#include "game/gamefile.h"
#include "game/datlexer.h"
#include "game/fsarchive.h"

ORIG_DATA(0061005C); /* CReadCursorDat::vftable */
ORIG_DATA(00610054); /* CSingleton<CReadCursorDat>::vftable */
ORIG_DATA(006CA2B4); /* the token the cursor loader read last */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006C9060); /* the numeric value of the last token (a float) */
ORIG_DATA(006C9068); /* the text of the last token */

inline void *operator new(unsigned int, void *p) { return p; }

extern "C" __declspec(dllimport) char *__cdecl _strlwr(char *s); /* 0x607414 */

/* The map's sentinel: a bare 0x48-byte node linking to itself.  It never carries a pair, so none is built. */
DECOMP(004A0750)
CursorRecordNode *__stdcall CreateCursorNodeSentinel()
{
    CursorRecordNode *node = (CursorRecordNode *)operator new(sizeof(CursorRecordNode));
    node->next = node;
    node->prev = node;
    return node;
}

/* The cursor map's constructor: the allocator byte from the caller, the node sentinel, a zero size and the nine
 * initial buckets all pointing at the sentinel.  Like the generic map ctors it returns the map in EAX. */
DECOMP(004A07F0)
FsHashMap *__thiscall InitCursorMap(FsHashMap *map, const unsigned char *allocator, const void *compare)
{
    *(unsigned char *)map = *allocator;
    map->sentinel = CreateCursorNodeSentinel();
    map->size = 0;
    void *sentinel = map->sentinel;
    InitPointerVector(&map->vectorAlloc, 9, &sentinel);
    map->mask = 1;
    map->count = 1;
    return map;
}

/* Empties the cursor map: every node's pair is destroyed (the text first, then the key) and the node freed.
 * The library's view of the map begins at FsHashMap+4, so the head sentinel is the map's field at +8 and the
 * size the field at +0xC. */
DECOMP(004430D0)
void __fastcall ClearCursorNodeList(char *mapObject)
{
    CursorRecordNode *head = *(CursorRecordNode **)(mapObject + 4);
    CursorRecordNode *node = head->next;
    head->next = head;
    head->prev = head;
    *(unsigned *)(mapObject + 8) = 0;
    while (node != head) {
        CursorRecordNode *next = node->next;
        node->pair.value.text.~basic_string();
        node->pair.key.~basic_string();
        operator delete(node);
        node = next;
    }
}

/* The cursor map's size guard (the library's map view starts four bytes into FsHashMap): growing past the
 * library's limit throws std::length_error, as in the other maps' guards. */
DECOMP(00442EC0)
void __thiscall AddCursorMapSize(void *mapObject, unsigned count)
{
    unsigned &size = *(unsigned *)((char *)mapObject + 8);
    if (0x3FFFFFFu - size < count)
        ThrowFsLengthError();
    size += count;
}

/* A fresh node: its links, then the pair copied behind them. */
DECOMP(00442FF0)
CursorRecordNode *__stdcall CreateCursorNode(CursorRecordNode *next, CursorRecordNode *prev,
                                             const CursorRecordPair *pair)
{
    CursorRecordNode *node = (CursorRecordNode *)operator new(sizeof(CursorRecordNode));
    node->next = next;
    node->prev = prev;
    ::new (&node->pair) CursorRecordPair(*pair);
    return node;
}

/* The pair operator[] builds for a missing key: the key and a copy of the default record.  The caller only
 * constructs the record's string, so the two numbers carry whatever the caller's stack held. */
DECOMP(00442CE0)
CursorRecordPair *__thiscall BuildCursorPair(CursorRecordPair *pair, const std::string *key,
                                             const CursorRecord *record)
{
    ::new (&pair->key) std::string(*key);
    ::new (&pair->value.text) std::string(record->text);
    pair->value.x = record->x;
    pair->value.y = record->y;
    return pair;
}

/* Inserts a cursor pair into the map: the key is hashed and looked up in its bucket (the nodes are ordered by
 * the case-sensitive std::string operator<), and a missing key is linked before its lower bound while the map
 * size grows.  The bucket starts that pointed at the lower bound must point at the new node instead. */
DECOMP(00443520)
FsInsertResult *__thiscall InsertCursorRecordNode(FsHashMap *map, FsInsertResult *result,
                                                  const CursorRecordPair *entry)
{
    if (map->count <= map->size >> 2)
        map->GrowBuckets(true);

    unsigned bucket = FsHashMap::HashName(&entry->key) & map->mask;
    if (map->count <= bucket)
        bucket += -1 - (map->mask >> 1);
    CursorRecordNode **buckets = (CursorRecordNode **)map->begin;
    CursorRecordNode *position = buckets[bucket + 1];
    if (position != buckets[bucket]) {
        do {
            position = position->prev;
            if (!(entry->key < position->pair.key)) {
                if (!(position->pair.key < entry->key)) {
                    result->node = position;
                    result->inserted = 0;
                    return result;
                }
                position = position->next;
                break;
            }
        } while (position != buckets[bucket]);
    }

    CursorRecordNode *node = CreateCursorNode(position, position->prev, entry);
    AddCursorMapSize((char *)map + 4, 1);
    position->prev = node;
    node->prev->next = node;

    CursorRecordNode *oldFirst = buckets[bucket];
    while (position == oldFirst && (buckets[bucket] = node, bucket != 0)) {
        bucket--;
        oldFirst = buckets[bucket];
    }
    result->node = node;
    result->inserted = 1;
    return result;
}

/* The map's operator[]: the record of the key, or a new node holding a default record.  The default record is
 * copied into a pair, the pair into the node, and then the temporaries are destroyed. */
DECOMP(004437E0)
CursorRecord *__thiscall CursorMapAtIndex(FsHashMap *map, const std::string *key)
{
    CursorRecordNode *node;
    map->FindName((FsStringNode **)&node, key);
    if (node == (CursorRecordNode *)map->sentinel) {
        alignas(CursorRecord) unsigned char recordStorage[sizeof(CursorRecord)];
        CursorRecord *record = (CursorRecord *)recordStorage;
        ::new (&record->text) std::string();
        alignas(CursorRecordPair) unsigned char pairStorage[sizeof(CursorRecordPair)];
        CursorRecordPair *pair = (CursorRecordPair *)pairStorage;
        BuildCursorPair(pair, key, record);
        FsInsertResult result;
        InsertCursorRecordNode(map, &result, pair);
        node = (CursorRecordNode *)result.node;
        pair->value.text.~basic_string();
        pair->key.~basic_string();
        record->text.~basic_string();
    }
    return &node->pair.value;
}

/* the original hands the map ctor an uninitialised stack byte for the empty allocator; nothing reads it */
DECOMP(004A0910)
CReadCursorDat::CReadCursorDat()
{
    char allocator = 0;
    vftable = d_0061005C;
    InitCursorMap(&map, (const unsigned char *)&allocator, &allocator);
}

DECOMP(004A0870)
CReadCursorDat::~CReadCursorDat()
{
    vftable = d_0061005C;

    if (map.begin)
        operator delete(map.begin);
    map.begin = nullptr;
    map.end = nullptr;
    map.limit = nullptr;

    /* the tree part at map+4 destroys the pairs and frees the nodes */
    ClearCursorNodeList((char *)&map + 4);
    if (map.sentinel)
        operator delete(map.sentinel);
    map.sentinel = nullptr;

    vftable = d_00610054;
}

/* Cursors.dat holds one 0x148 block: a token that is skipped, then entries of a name (lowercased into the key),
 * a texture name and two numbers, up to the 0x103 close.  The loader reads the file whole through the shared
 * CGameFile, like the interface loader. */
DECOMP(004A0990)
void CReadCursorDat::Load()
{
    CGameFile *reader = (CGameFile *)d_006CA280;
    reader->Open("Cursors.dat", 1);
    ORIG_VAR(006CA278, unsigned) = reader->file->size;

    std::string name;
    std::string text;
    ORIG_VAR(006CA2B4, int) = DatLexerNextToken();
    while (ORIG_VAR(006CA2B4, int) != 0) {
        if (ORIG_VAR(006CA2B4, int) == 0x148) {
            DatLexerNextToken();
            ORIG_VAR(006CA2B4, int) = DatLexerNextToken();
            if (ORIG_VAR(006CA2B4, int) != 0x103) {
                do {
                    _strlwr(d_006C9068);
                    name = (const char *)d_006C9068;
                    DatLexerNextToken();
                    text = (const char *)d_006C9068;
                    DatLexerNextToken();
                    unsigned x = (unsigned)(int)ORIG_VAR(006C9060, float);
                    DatLexerNextToken();
                    unsigned y = (unsigned)(int)ORIG_VAR(006C9060, float);

                    CursorRecord *record = CursorMapAtIndex(&map, &name);
                    record->text = text;
                    record->x = x;
                    record->y = y;
                    ORIG_VAR(006CA2B4, int) = DatLexerNextToken();
                } while (ORIG_VAR(006CA2B4, int) != 0x103);
            }
        }
        ORIG_VAR(006CA2B4, int) = DatLexerNextToken();
    }
    reader->Close();
}
