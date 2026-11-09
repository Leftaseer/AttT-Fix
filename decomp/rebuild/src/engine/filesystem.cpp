/* CFileSystem: the pak archive file system - opening the ResourceN.pak chain, opening files from the paks or
 * from disk, and the lifetime of all of it (0x451E00 / 0x451E90 / 0x4514B0 / 0x452580). */
#include "game/common.h"
#include "game/globals.h"
#include "game/config.h"
#include "game/filesystem.h"
#include "game/fsarchive.h"

ORIG_DATA(0060B140); /* CSingleton<CFileSystem>::vftable */
ORIG_DATA(0060B1A8); /* CFileSystem::vftable */
ORIG_DATA(0060B214); /* vtable of the file stream class (deleting dtor 0x4524E0) the pak streams carry at +58 */
ORIG_DATA(0060B1AC); /* "the archive signature does not match the required one..." */
ORIG_DATA(0060B1E0); /* ".\\FileSystem.cpp" */
ORIG_DATA(0060B1F4); /* "cannot open the file - " */
ORIG_DATA(00607BC8); /* "Ошибка при создании m_instance в CSingleton" */
ORIG_DATA(00607E98); /* "e:\\prog\\att1\\singleton.h" */
ORIG_DATA(006C04B4); /* the 16-byte key of the version 200 paks */
ORIG_DATA(006C7C90); /* the cp1251 lowercasing table {0..255}: A-Z and the Cyrillic capitals (and the 0xA8) fold */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

/* the file system library's maps and files (their bodies stay generated; see the comments at the call sites) */
ORIG_THISCALL(00451430, void, (void *map, const void *alloc, const void *comp)); /* ctor of map<string, PakEntry> */
ORIG_THISCALL(00489710, void, (void *map, const void *alloc, const void *comp)); /* ctor of map<int, ifstream*> */
ORIG_THISCALL(00553E40, void, (void *vector, unsigned count, const void *value)); /* resize the bucket vector */
ORIG_THISCALL(00450AE0, void *, (void *self, void *stream, unsigned size, unsigned offset, bool encrypted));
ORIG_THISCALL(00450B20, void *, (void *self, const std::string *name));
ORIG_FASTCALL(005224A0, void, (void *self));                                  /* break the string map's node list */
ORIG_THISCALL(004EF350, void, (void *self, unsigned count, void *sentinelPtr)); /* refill the bucket vector */
ORIG_FASTCALL(004EF7F0, void, (void *self));                                  /* clear the int map */

/* the exe imports operator new (?2) but implements new[]/?_U itself as a jmp to it; delete[] is imported */
ORIG_FN(005E3B10, void *, (unsigned int size)); /* operator new[] */
inline void *operator new(unsigned int, void *p) { return p; }

extern "C" __declspec(dllimport) char *__cdecl _strlwr(char *s);

/* the CRT's long division, returned in EDX:EAX like MSVCR80's _ldiv */
struct LDivResult {
    long quot;
    long rem;
};
DECOMP_C LDivResult(__cdecl *imp_006073C0)(long, long) __asm__("__imp__ldiv");

/* The bucket of a key: the library's hash scrambles it by dividing through a prime and mixing the quotient and
 * the remainder; the bucket count is a power of two, and the range of a bucket ends where the next one starts. */
DECOMP(00450D20)
unsigned FsHashMap::BucketIndex(const unsigned *key) const
{
    LDivResult part = imp_006073C0((long)(*key ^ 0xdeadbeef), 0x1f31d);
    unsigned bucket = (unsigned)part.rem * 0x41a7u + (unsigned)part.quot * (unsigned)-0xb14;
    if ((int)bucket < 0)
        bucket += 0x7fffffff;
    bucket &= mask;
    if (count <= bucket)
        bucket += -1 - (mask >> 1);
    return bucket;
}

/* Finds a node of an int-keyed map; every bucket is a range of the map's one node list (the bucket holds its
 * first node, the next bucket's entry ends it). A key sorts into the list, so a greater node ends the search. */
DECOMP(00450DA0)
void FsHashMap::FindInt(FsIntNode **node, const int *key) const
{
    FsIntNode **buckets = (FsIntNode **)begin;
    unsigned bucket = BucketIndex((const unsigned *)key);
    FsIntNode *endNode = buckets[bucket + 1];
    for (FsIntNode *it = buckets[bucket]; it != endNode; it = it->next) {
        if (*key <= it->key) {
            if (it->key <= *key) {
                *node = it;
                return;
            }
            break;
        }
    }
    *node = (FsIntNode *)sentinel;
}

/* The case-insensitive map's string hash: every (size/16+1)-st byte, lowercased through the cp1251 table, is
 * added to 0xDEADBEEF.  The bucket of a key is this value masked, with no prime mixing (unlike HashName). */
DECOMP(00579BB0)
unsigned __stdcall HashStringNoCase(const std::string *key)
{
    const char *data = key->c_str();
    const unsigned size = key->size();
    unsigned hash = 0xdeadbeefu;
    if (size != 0) {
        const unsigned step = (size >> 4) + 1;
        for (unsigned i = 0; i <= size - step; i += step)
            hash += ((const unsigned char *)d_006C7C90)[(unsigned char)data[i]];
    }
    return hash;
}

/* The case-insensitive ordering of that map: the lowercased bytes decide a common prefix, and equal prefixes
 * order by length.  Like the library's comparator it returns a bool (a strict less-than). */
DECOMP(00579C00)
bool __stdcall LessStringNoCase(const std::string *a, const std::string *b)
{
    const unsigned sizeA = a->size();
    const unsigned sizeB = b->size();
    const unsigned char *pa = (const unsigned char *)a->c_str();
    const unsigned char *pb = (const unsigned char *)b->c_str();
    const unsigned char *table = (const unsigned char *)d_006C7C90;
    unsigned common = sizeA < sizeB ? sizeA : sizeB;
    if (common != 0) {
        unsigned i = 0;
        while (--common != 0 && table[pa[i]] == table[pb[i]])
            i++;
        if (table[pa[i]] != table[pb[i]])
            return table[pa[i]] < table[pb[i]];
    }
    return sizeA < sizeB;
}

/* The string-keyed twin of FindInt: every bucket is a range of the one node list, the keys are ordered
 * case-insensitively, and a greater key ends the search. */
DECOMP(00450E60)
void FsHashMap::FindString(FsStringNode **node, const std::string *key) const
{
    FsStringNode **buckets = (FsStringNode **)begin;
    unsigned bucket = HashStringNoCase(key) & mask;
    if (count <= bucket)
        bucket += -1 - (mask >> 1);
    FsStringNode *endNode = buckets[bucket + 1];
    for (FsStringNode *it = buckets[bucket]; it != endNode; it = it->next) {
        if (!LessStringNoCase(&it->key, key)) {
            if (!LessStringNoCase(key, &it->key)) {
                *node = it;
                return;
            }
            break;
        }
    }
    *node = (FsStringNode *)sentinel;
}

/* FNV-1a over the whole string, then the library's prime to spread it: the hash of the case-sensitive maps */
DECOMP(00422A20)
unsigned FsHashMap::HashName(const std::string *key)
{
    unsigned hash = 0x811c9dc5;
    const char *data = key->c_str();
    for (unsigned i = 0; i < key->size(); i++)
        hash = hash * 0x1000193u ^ (int)data[i];
    LDivResult part = imp_006073C0((long)hash, 0x1f31d);
    unsigned value = (unsigned)part.rem * 0x41a7u + (unsigned)part.quot * (unsigned)-0xb14;
    if ((int)value < 0)
        value += 0x7fffffff;
    return value;
}

/* the case-sensitive find of the file directory map: the same bucket ranges, ordered by std::string's operator< */
DECOMP(00422D80)
void FsHashMap::FindName(FsStringNode **node, const std::string *key) const
{
    FsStringNode **buckets = (FsStringNode **)begin;
    unsigned bucket = HashName(key) & mask;
    if (count <= bucket)
        bucket += -1 - (mask >> 1);
    FsStringNode *endNode = buckets[bucket + 1];
    for (FsStringNode *it = buckets[bucket]; it != endNode; it = it->next) {
        if (!(it->key < *key)) {
            if (!(*key < it->key)) {
                *node = it;
                return;
            }
            break;
        }
    }
    *node = (FsStringNode *)sentinel;
}

/* The fill constructor of a bucket vector.  The vector's own allocator byte stays as it was; the three
 * pointers start empty, then an allocation of count pointers is filled with copies of *value.  The original
 * allocates through the vector's allocator (0x4DEE50), whose overflow guard the length check makes unreachable. */
DECOMP(004CCC80)
void __thiscall InitPointerVector(void *vector, unsigned count, const void *value)
{
    void **begin = (void **)((char *)vector + 4);
    begin[0] = nullptr;
    begin[1] = nullptr;
    begin[2] = nullptr;
    if (count == 0)
        return;
    if (count > 0x3FFFFFFFu)
        ThrowVectorLengthError();
    void **data = (void **)operator new(count * 4);
    begin[2] = data + count;
    begin[0] = data;
    begin[1] = data;
    for (unsigned i = 0; i < count; i++)
        data[i] = *(void *const *)value;
    begin[1] = data + count;
}

/* The two map constructors: an empty node list through a sentinel sized for the map's node, a zero size and
 * the nine slots of the initial bucket vector all holding the sentinel; the allocator byte comes from the
 * caller and the comparison object is never read.  Both return the map in EAX, as the ctors do. */
DECOMP(00451430)
FsHashMap *FsHashMap::InitStringMap(const unsigned char &allocator, const void *compare)
{
    *(unsigned char *)this = allocator;
    FsStringNode *head = (FsStringNode *)operator new(0x30);
    head->next = head;
    head->prev = head;
    sentinel = head;
    size = 0;
    void *headValue = head;
    InitPointerVector(&vectorAlloc, 9, &headValue);
    mask = 1;
    count = 1;
    return this;
}

DECOMP(00489710)
FsHashMap *FsHashMap::InitIntMap(const unsigned char &allocator, const void *compare)
{
    *(unsigned char *)this = allocator;
    FsIntNode *head = (FsIntNode *)operator new(0x10);
    head->next = head;
    head->prev = head;
    sentinel = head;
    size = 0;
    void *headValue = head;
    InitPointerVector(&vectorAlloc, 9, &headValue);
    mask = 1;
    count = 1;
    return this;
}

/* Empties the node list of an int-keyed map and resets its buckets to the initial nine-slot vector. */
DECOMP(004EF7F0)
void FsHashMap::ClearInt()
{
    FsIntNode *head = (FsIntNode *)sentinel;
    FsIntNode *node = head->next;
    head->next = head;
    head->prev = head;
    size = 0;
    while (node != head) {
        FsIntNode *next = node->next;
        operator delete(node);
        node = next;
    }
    void *headValue = head;
    sub_004EF350(&vectorAlloc, 9, &headValue);
    mask = 1;
    count = 1;
}

/* Empties the node list of a string-keyed map, destroying the keys.  The library's view of the map begins at
 * FsHashMap+4, so the head sentinel is the map's field at +8 and the size the field at +0xC. */
DECOMP(005224A0)
void __fastcall ClearStringNodeList(char *mapObject)
{
    FsStringNode *head = *(FsStringNode **)(mapObject + 4);
    FsStringNode *node = head->next;
    head->next = head;
    head->prev = head;
    *(unsigned *)(mapObject + 8) = 0;
    while (node != head) {
        FsStringNode *next = node->next;
        node->key.~basic_string();
        operator delete(node);
        node = next;
    }
}

/* the two node factories of the inserts: the node's links and then the value copied from the caller's entry */
DECOMP(00451000)
FsPakNode *__stdcall CreatePakNode(FsStringNode *next, FsStringNode *prev, const PakEntry *entry)
{
    FsPakNode *node = (FsPakNode *)operator new(sizeof(FsPakNode));
    node->next = next;
    node->prev = prev;
    new (&node->value) PakEntry(*entry);
    return node;
}

DECOMP(00489070)
FsIntNode *__stdcall CreateStreamNode(FsIntNode *next, FsIntNode *prev, const int *entry)
{
    FsIntNode *node = (FsIntNode *)operator new(sizeof(FsIntNode));
    node->next = next;
    node->prev = prev;
    node->key = entry[0];
    node->value = (void *)((const unsigned *)entry)[1];
    return node;
}

/* The map size guards: the library's nodes are limited by their allocation size (0x28 bytes for the file
 * entries, 0x10 for the streams); growing past the limit throws std::length_error.  The guards see the
 * library's map view, which starts four bytes into FsHashMap. */
DECOMP(004E66E0)
void __thiscall AddStringMapSize(void *mapObject, unsigned count)
{
    unsigned &size = *(unsigned *)((char *)mapObject + 8);
    if (0x6666666u - size < count)
        ThrowFsLengthError();
    size += count;
}

DECOMP(004EB9C0)
void __thiscall AddIntMapSize(void *mapObject, unsigned count)
{
    unsigned &size = *(unsigned *)((char *)mapObject + 8);
    if (0x1fffffffu - size < count)
        ThrowFsLengthError();
    size += count;
}

/* The library's table growth, the same in both inserts: once a bucket holds more than four nodes the mask
 * grows and the bucket vector doubles; then the nodes of the last bucket that no longer hash into it are
 * spliced to the end of the node list, where they form the new bucket.  The trailing buckets that ended at
 * the sentinel must start at the first moved node instead. */
void FsHashMap::GrowBuckets(bool stringKeys)
{
    unsigned slots = begin ? (unsigned)(((char *)end - (char *)begin) / 4) : 0;
    if (count < slots - 1) {
        if (mask < count)
            mask = mask * 2 + 1;
    } else {
        mask = slots * 2 - 3;
        sub_00553E40(&vectorAlloc, slots * 2 - 1, sentinel);
    }

    unsigned split = count - (mask >> 1) - 1;
    FsStringNode **buckets = (FsStringNode **)begin;
    FsStringNode *node = buckets[split];
    unsigned here = split;
    if (node != buckets[split + 1]) {
        do {
            FsStringNode *next = node->next;
            const void *key = (char *)node + 8;
            unsigned hash;
            if (stringKeys) {
                hash = HashName((const std::string *)key);
            } else {
                /* the int hash before the bucket fold: the masked value alone decides the split */
                LDivResult part = imp_006073C0((long)(*(const unsigned *)key ^ 0xdeadbeef), 0x1f31d);
                hash = (unsigned)part.rem * 0x41a7u + (unsigned)part.quot * (unsigned)-0xb14;
                if ((int)hash < 0)
                    hash += 0x7fffffff;
            }
            if ((hash & mask) != split) {
                if (next != (FsStringNode *)sentinel) {
                    /* the moved node no longer belongs to the split bucket's range */
                    FsStringNode *first = buckets[here];
                    while (node == first && (buckets[here] = next, here != 0)) {
                        here--;
                        first = buckets[here];
                    }
                    FsStringNode *head = (FsStringNode *)sentinel;
                    node->prev->next = next;
                    node->next = head;
                    head->prev->next = node;
                    FsStringNode *last = head->prev;
                    head->prev = node;
                    next->prev = node->prev;
                    node->prev = last;
                    node = head->prev;
                    buckets[count + 1] = head;
                    here = split;
                }
                for (unsigned b = count; here < b && buckets[b] == (FsStringNode *)sentinel; b--)
                    buckets[b] = node;
                if (next == (FsStringNode *)sentinel)
                    break;
            }
            node = next;
        } while (node != buckets[here + 1]);
    }
    count++;
}

/* Inserts a file directory entry: the key is hashed and looked up in its bucket (the nodes are ordered by the
 * case-sensitive std::string operator<), and a missing key is linked before its lower bound and the size
 * grows.  The bucket starts that pointed at the lower bound must point at the new node instead. */
DECOMP(00451770)
void FsHashMap::InsertName(FsInsertResult *result, const PakEntry *entry)
{
    if (count <= size >> 2)
        GrowBuckets(true);

    unsigned bucket = HashName(&entry->name) & mask;
    if (count <= bucket)
        bucket += -1 - (mask >> 1);
    FsStringNode **buckets = (FsStringNode **)begin;
    FsStringNode *position = buckets[bucket + 1];
    if (position != buckets[bucket]) {
        do {
            position = position->prev;
            if (!(entry->name < position->key)) {
                if (!(position->key < entry->name)) {
                    result->node = position;
                    result->inserted = 0;
                    return;
                }
                position = position->next;
                break;
            }
        } while (position != buckets[bucket]);
    }

    FsPakNode *allocated = CreatePakNode(position, position->prev, entry);
    FsStringNode *node = (FsStringNode *)allocated;
    AddStringMapSize((char *)this + 4, 1);
    position->prev = node;
    node->prev->next = node;

    FsStringNode *oldFirst = buckets[bucket];
    while (position == oldFirst && (buckets[bucket] = node, bucket != 0)) {
        bucket--;
        oldFirst = buckets[bucket];
    }
    result->node = node;
    result->inserted = 1;
}

/* The int-keyed twin of InsertName: the nodes are ordered by their int keys and both the bucket of a node
 * and of the new key come from BucketIndex. */
DECOMP(00451A50)
void FsHashMap::InsertInt(FsInsertResult *result, const int *entry)
{
    if (count <= size >> 2)
        GrowBuckets(false);

    unsigned bucket = BucketIndex((const unsigned *)entry);
    FsIntNode **buckets = (FsIntNode **)begin;
    FsIntNode *position = buckets[bucket + 1];
    if (position != buckets[bucket]) {
        do {
            position = position->prev;
            if (position->key <= entry[0]) {
                if (entry[0] <= position->key) {
                    result->node = position;
                    result->inserted = 0;
                    return;
                }
                position = position->next;
                break;
            }
        } while (position != buckets[bucket]);
    }

    FsIntNode *node = CreateStreamNode(position, position->prev, entry);
    AddIntMapSize((char *)this + 4, 1);
    position->prev = node;
    node->prev->next = node;

    FsIntNode *oldFirst = buckets[bucket];
    while (position == oldFirst && (buckets[bucket] = node, bucket != 0)) {
        bucket--;
        oldFirst = buckets[bucket];
    }
    result->node = node;
    result->inserted = 1;
}

static void ThrowFsError(const std::string &msg, int line)
{
    CGameException e(msg, ORIG_STR(0060B1E0), line);
    _CxxThrowException(&e, d_0069916C);
    __builtin_unreachable();
}

/* The singleton accessor: the file system is built on the first request and a failed allocation throws */
DECOMP(0044ABE0)
CFileSystem *CFileSystem::Instance()
{
    if (!g_fileSystemInstance) {
        void *memory = operator new(sizeof(CFileSystem));
        g_fileSystemInstance = memory ? new (memory) CFileSystem() : nullptr;
        if (!g_fileSystemInstance)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607E98), 16);
    }
    return g_fileSystemInstance;
}

DECOMP(00451E00)
CFileSystem::CFileSystem()
{
    /* the original hands the map constructors the address of an uninitialised stack byte for the empty
     * allocator; nothing ever reads the value */
    char allocator = 0;
    vftable = d_0060B1A8;
    files.InitStringMap(allocator, &allocator);
    streams.InitIntMap(allocator, &allocator);
    lastEntry = nullptr;
    InitFolder(reinterpret_cast<FsFolder *>(embedded));
}

/* The archive name at +0x60 is destroyed by the compiler-generated part of this destructor after the body; the
 * original destroys it between the embedded string and the map frees, which is unobservable. */
DECOMP(00452580)
CFileSystem::~CFileSystem()
{
    vftable = d_0060B1A8;

    /* break the files node list (0x5224A0 works on the tree part at map+4) and refill its 9 empty buckets */
    ClearStringNodeList((char *)&files + 4);
    void *filesSentinel = files.sentinel;
    sub_004EF350(&files.vectorAlloc, 9, &filesSentinel);
    files.mask = 1;
    files.count = 1;

    /* close every pak stream (through its deleting dtor) */
    FsIntNode *streamEnd = (FsIntNode *)streams.sentinel;
    for (FsIntNode *node = streamEnd->next; node != streamEnd; node = node->next)
        delete (std::ifstream *)node->value;

    streams.ClearInt();

    /* the embedded archive folder: its children list, the sentinel and the name string */
    DestroyFolder(reinterpret_cast<FsFolder *>(embedded));

    /* the rest of the maps: the bucket vectors, the nodes left by the generic map destructors and the sentinels */
    if (streams.begin)
        operator delete(streams.begin);
    streams.begin = nullptr;
    streams.end = nullptr;
    streams.limit = nullptr;
    FsIntNode *intSentinel = (FsIntNode *)streams.sentinel;
    FsIntNode *intNode = intSentinel->next;
    intSentinel->next = intSentinel;
    intSentinel->prev = intSentinel;
    streams.size = 0;
    while (intNode != intSentinel) {
        FsIntNode *next = intNode->next;
        operator delete(intNode);
        intNode = next;
    }
    operator delete(streams.sentinel);
    streams.sentinel = nullptr;

    if (files.begin)
        operator delete(files.begin);
    files.begin = nullptr;
    files.end = nullptr;
    files.limit = nullptr;
    FsStringNode *stringSentinel = (FsStringNode *)files.sentinel;
    FsStringNode *stringNode = stringSentinel->next;
    stringSentinel->next = stringSentinel;
    stringSentinel->prev = stringSentinel;
    files.size = 0;
    while (stringNode != stringSentinel) {
        FsStringNode *next = stringNode->next;
        stringNode->key.~basic_string();
        operator delete(stringNode);
        stringNode = next;
    }
    operator delete(files.sentinel);
    files.sentinel = nullptr;

    vftable = d_0060B140;
}

/* Opens the ResourceN.pak chain: <folder of the exe>Resource0.pak, then Resource1.pak, ... The first pak that
 * cannot be opened ends the chain (a missing Resource0.pak is fatal). Every file of every pak goes into the
 * files map; a later pak overrides the same name of an earlier one. */
DECOMP(00451E90)
void CFileSystem::OpenPaks(const std::string &name)
{
    archiveName = name;
    bool isPak = archiveName.substr(archiveName.size() - 4, archiveName.size()) == ".pak";
    paksOpened = isPak;
    if (!isPak)
        return;

    nCfg::GamePath *gamePath = (nCfg::GamePath *)g_gamePath;
    unsigned int i = 0;
    for (;; i++) {
        char digits[16];
        sprintf(digits, "%d", (int)i);
        std::string pakName = gamePath->exePath + "Resource" + digits + ".pak";
        archiveName = pakName;

        /* the stream is an MSVCP80 ifstream with 0x34 bytes of the file system class around it: its own vtable
         * sits at +0x58 of the 0x8C-byte object */
        std::ifstream *stream = (std::ifstream *)operator new(0x8C);
        new (stream) std::ifstream(pakName.c_str(), 0x21, 0x40);
        *(void **)((char *)stream + 0x58) = d_0060B214;
        currentStream = stream;
        if (stream->fail())
            break;

        struct {
            int index;
            std::ifstream *stream;
        } streamEntry = {(int)i, stream};
        FsInsertResult inserted;
        streams.InsertInt(&inserted, &streamEntry.index);

        char header[12];
        stream->read(header, sizeof header);
        if (header[0] != 'G' || header[1] != 'R' || header[2] != 'E' || header[3] != 'S') {
            stream->close();
            ThrowFsError(std::string(ORIG_STR(0060B1AC)), 0x67);
        }
        pakVersion = *(int *)(header + 4);
        pakCount = *(int *)(header + 8);
        unsigned char *key = (unsigned char *)d_006C04B4;
        if (pakVersion == 200) {
            /* the four bytes at +08 are part of the header too but nothing ever reads them */
            for (int j = 0; j < 4; j++)
                unused08[j] ^= key[j];
            for (int j = 0; j < 4; j++)
                ((unsigned char *)&pakCount)[j] ^= key[4 + j];
        }

        /* new[] gets the size saturated on 32-bit overflow; the read and the decrypt loop use the wrapped one */
        unsigned int size = (unsigned int)pakCount * 0x88;
        unsigned long long bytes = (unsigned long long)pakCount * 0x88;
        PakRecord *records = (PakRecord *)sub_005E3B10((unsigned int)(bytes >> 32) ? 0xFFFFFFFFu : size);
        stream->read((char *)records, size);
        if (pakVersion == 200)
            for (unsigned int j = 0; j < size; j++)
                ((unsigned char *)records)[j] ^= key[j % 16];

        for (unsigned int k = 0; k < (unsigned int)pakCount; k++) {
            PakRecord &record = records[k];
            if (i == 0) {
                PakEntry entry;
                entry.name = record.name;
                entry.offset = record.offset;
                entry.size = record.size;
                entry.pak = 0;
                FsInsertResult inserted;
                files.InsertName(&inserted, &entry);
            } else {
                std::string keyName(record.name);
                FsStringNode *node;
                files.FindName(&node, &keyName);
                if (node == (FsStringNode *)files.sentinel) {
                    PakEntry entry;
                    entry.name = keyName;
                    entry.offset = record.offset;
                    entry.size = record.size;
                    entry.pak = (int)i;
                    FsInsertResult inserted;
                    files.InsertName(&inserted, &entry);
                } else {
                    unsigned *value = (unsigned *)((char *)node + 0x24);
                    value[0] = record.offset;
                    value[1] = record.size;
                    value[2] = i;
                }
            }
        }
        operator delete[](records);
    }

    if (i == 0)
        ThrowFsError(ORIG_STR(0060B1F4) + archiveName, 0x58);
}

/* A name without a drive is looked up in the archive's prefix map: a known name resolves to its mapped
 * directory followed by the name, an unknown one fails. */
DECOMP(00451220)
bool CFileSystem::ResolvePath(const std::string &name, std::string *path)
{
    FsStringNode *node;
    prefixes->FindString(&node, &name);
    if (node == (FsStringNode *)prefixes->sentinel)
        return false;
    *path = **(std::string **)((char *)node + 0x24) + name;
    return true;
}

/* Opens a file by name. With no open paks (or a name with a drive) the file is taken from disk; a name without
 * a drive first goes through the embedded file system's path prefixes. With open paks, a name is looked up in
 * the pak directories (lowercased) and comes back as a section of its pak stream; a missing name returns 0. */
DECOMP(004514B0)
void *CFileSystem::OpenFile(const std::string &name)
{
    if (!paksOpened || name.find(":", 0) != std::string::npos) {
        if (name.find(':', 0) == std::string::npos) {
            std::string path;
            if (ResolvePath(name, &path)) {
                void *file = operator new(0x98);
                return file ? sub_00450B20(file, &path) : nullptr;
            }
            return nullptr;
        }

        std::ifstream probe(name.c_str(), std::ios_base::_In, std::ios_base::_Openprot);
        if (probe) {
            void *file = operator new(0x98);
            if (file)
                file = sub_00450B20(file, &name);
            probe.close();
            return file;
        }
        return nullptr;
    }

    /* the pak names are kept lowercased */
    char lower[256];
    char *dst = lower;
    const char *src = name.c_str();
    while ((*dst++ = *src++) != '\0')
        ;
    _strlwr(lower);
    std::string key(lower);
    FsStringNode *node;
    files.FindName(&node, &key);
    lastEntry = node;
    if ((void *)node == files.sentinel)
        return nullptr;

    void *file = operator new(0x1C);
    if (!file)
        return nullptr;
    int pak = *(int *)((char *)node + 0x2C);
    FsIntNode *streamNode;
    streams.FindInt(&streamNode, &pak);
    return sub_00450AE0(file, streamNode->value, *(unsigned *)((char *)node + 0x28),
                        *(unsigned *)((char *)node + 0x24), pakVersion == 200);
}
