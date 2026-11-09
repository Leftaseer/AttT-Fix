/* CFileSystem: the pak archive file system - opening the ResourceN.pak chain, opening files from the paks or
 * from disk, and the lifetime of all of it (0x451E00 / 0x451E90 / 0x4514B0 / 0x452580). */
#include "game/common.h"
#include "game/globals.h"
#include "game/config.h"
#include "game/filesystem.h"

ORIG_DATA(0060B140); /* CSingleton<CFileSystem>::vftable */
ORIG_DATA(0060B1A8); /* CFileSystem::vftable */
ORIG_DATA(0060B214); /* vtable of the file stream class (deleting dtor 0x4524E0) the pak streams carry at +58 */
ORIG_DATA(0060B1AC); /* "the archive signature does not match the required one..." */
ORIG_DATA(0060B1E0); /* ".\\FileSystem.cpp" */
ORIG_DATA(0060B1F4); /* "cannot open the file - " */
ORIG_DATA(006C04B4); /* the 16-byte key of the version 200 paks */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

/* the file system library's maps and files (their bodies stay generated; see the comments at the call sites) */
ORIG_THISCALL(00451430, void, (void *map, const void *alloc, const void *comp)); /* ctor of map<string, PakEntry> */
ORIG_THISCALL(00489710, void, (void *map, const void *alloc, const void *comp)); /* ctor of map<int, ifstream*> */
ORIG_FASTCALL(00577C60, void *, (void *self));                                  /* ctor of the embedded fs object */
ORIG_THISCALL(00451770, void, (void *map, void *result, const void *value));    /* insert a name in files */
ORIG_THISCALL(00451A50, void, (void *map, void *result, const void *value));    /* insert a stream in streams */
ORIG_THISCALL(00422D80, void, (void *map, void *node, const std::string *key)); /* find a name in files */
ORIG_THISCALL(00450AE0, void *, (void *self, void *stream, unsigned size, unsigned offset, bool encrypted));
ORIG_THISCALL(00450B20, void *, (void *self, const std::string *name));
ORIG_FASTCALL(005224A0, void, (void *self));                                  /* break the string map's node list */
ORIG_THISCALL(004EF350, void, (void *self, unsigned count, void *sentinelPtr)); /* refill the bucket vector */
ORIG_FASTCALL(004EF7F0, void, (void *self));                                  /* clear the int map */
ORIG_FASTCALL(00450F30, void, (void *self));                                  /* clear the embedded map */

/* the hash map's case-folding string hash and its case-insensitive ordering (both pop their arguments) */
ORIG_STDCALL(00579BB0, unsigned, (const std::string *key));
ORIG_STDCALL(00579C00, bool, (const std::string *a, const std::string *b));

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

/* The string-keyed twin of FindInt: every bucket is a range of the one node list, the keys are ordered
 * case-insensitively, and a greater key ends the search. */
DECOMP(00450E60)
void FsHashMap::FindString(FsStringNode **node, const std::string *key) const
{
    FsStringNode **buckets = (FsStringNode **)begin;
    unsigned bucket = sub_00579BB0(key) & mask;
    if (count <= bucket)
        bucket += -1 - (mask >> 1);
    FsStringNode *endNode = buckets[bucket + 1];
    for (FsStringNode *it = buckets[bucket]; it != endNode; it = it->next) {
        if (!sub_00579C00(&it->key, key)) {
            if (!sub_00579C00(key, &it->key)) {
                *node = it;
                return;
            }
            break;
        }
    }
    *node = (FsStringNode *)sentinel;
}

static void ThrowFsError(const std::string &msg, int line)
{
    CGameException e(msg, ORIG_STR(0060B1E0), line);
    _CxxThrowException(&e, d_0069916C);
    __builtin_unreachable();
}

DECOMP(00451E00)
CFileSystem::CFileSystem()
{
    /* the original hands the map constructors the address of an uninitialised stack byte for the empty
     * allocator; nothing ever reads the value */
    char allocator = 0;
    vftable = d_0060B1A8;
    sub_00451430(&files, &allocator, &allocator);
    sub_00489710(&streams, &allocator, &allocator);
    lastEntry = nullptr;
    sub_00577C60(embedded);
}

/* The archive name at +0x60 is destroyed by the compiler-generated part of this destructor after the body; the
 * original destroys it between the embedded string and the map frees, which is unobservable. */
DECOMP(00452580)
CFileSystem::~CFileSystem()
{
    vftable = d_0060B1A8;

    /* break the files node list (0x5224A0 works on the tree part at map+4) and refill its 9 empty buckets */
    sub_005224A0((char *)&files + 4);
    void *filesSentinel = files.sentinel;
    sub_004EF350(&files.vectorAlloc, 9, &filesSentinel);
    files.mask = 1;
    files.count = 1;

    /* close every pak stream (through its deleting dtor) */
    FsIntNode *streamEnd = (FsIntNode *)streams.sentinel;
    for (FsIntNode *node = streamEnd->next; node != streamEnd; node = node->next)
        delete (std::ifstream *)node->value;

    sub_004EF7F0(&streams);

    /* the embedded file system object: the map at +1C, its sentinel and its string at +0 (the bytes are opaque
     * here, so that string needs destroying by hand; the archive name at +60 is a member and goes by itself) */
    sub_00450F30(embedded + 0x1C);
    void *&embeddedSentinel = *(void **)(embedded + 0x20);
    operator delete(embeddedSentinel);
    embeddedSentinel = nullptr;
    ((std::basic_string<char> *)embedded)->~basic_string<char>();

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
        void *inserted[2];
        sub_00451A50(&streams, inserted, &streamEntry);

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
                void *inserted2[2];
                sub_00451770(&files, inserted2, &entry);
            } else {
                std::string keyName(record.name);
                FsStringNode *node;
                sub_00422D80(&files, &node, &keyName);
                if (node == (FsStringNode *)files.sentinel) {
                    PakEntry entry;
                    entry.name = keyName;
                    entry.offset = record.offset;
                    entry.size = record.size;
                    entry.pak = (int)i;
                    void *inserted2[2];
                    sub_00451770(&files, &inserted2, &entry);
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
    sub_00422D80(&files, &node, &key);
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
