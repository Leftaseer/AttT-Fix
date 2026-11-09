/* The file objects of the engine's file system: the abstract base file, a section of a pak, and a file on disk.
 *
 * The base file's vtable (0x60B148) is the file interface: [0] the deleting destructor, [1] read(buf, n),
 * [2] seek(pos), [3] advance(delta), [4] tell().  CArchFile (vtable 0x60B160) is a range of a pak stream shared
 * by the file system, XOR-decrypting the first 16 bytes of version 200 paks; CFstreamFile (0x60B18C) owns an
 * MSVCP80 std::ifstream and reads the file straight from disk.  CFileSystem::OpenFile builds one or the other. */
#pragma once
#include "game/common.h"

struct CBaseFile {
    void *vftable;  /* +00 0x60B148 */
    int objectFlag; /* +04 the CGameObject flag its base destructor checks */
    unsigned size;  /* +08 size of the file in bytes */

    CBaseFile();              /* 0x450A80 */
    ~CBaseFile();             /* 0x450AA0 frees nothing itself (the derived object already did) */
    void *Destroy(int flags); /* 0x450AB0 the deleting destructor: frees the object when bit 0 of flags is set */
};
static_assert(sizeof(CBaseFile) == 0xC, "CBaseFile is 0xC bytes");
static_assert(__builtin_offsetof(CBaseFile, size) == 0x8, "CBaseFile::size");

/* a file kept inside a pak: the pak's stream, the read position, the file's start in the pak and the encryption
 * flag; 0x4508C0 (src/fixed/f_004508C0.c) implements the read over those fields */
struct CArchFile : CBaseFile {
    void *stream;      /* +0C the std::ifstream of the pak (owned by the file system's stream map) */
    unsigned position; /* +10 the read position inside the file */
    unsigned offset;   /* +14 where the file starts in the pak */
    bool encrypted;    /* +18 XOR the first 16 bytes of the file with the key at 0x6C04B4 */
    unsigned char pad19[3];

    CArchFile(void *stream, unsigned size, unsigned offset, bool encrypted); /* 0x450AE0 */
    unsigned Read(void *buf, unsigned n);                                    /* 0x4508C0 (src/fixed) */
    unsigned Seek(unsigned pos);                                             /* 0x42B630 */
    unsigned Advance(unsigned delta);                                        /* 0x450B10 */
    unsigned Tell();                                                         /* 0x5B42C0 */
};
static_assert(sizeof(CArchFile) == 0x1C, "CArchFile is 0x1C bytes");
static_assert(__builtin_offsetof(CArchFile, stream) == 0x0C, "CArchFile::stream");
static_assert(__builtin_offsetof(CArchFile, position) == 0x10, "CArchFile::position");
static_assert(__builtin_offsetof(CArchFile, offset) == 0x14, "CArchFile::offset");
static_assert(__builtin_offsetof(CArchFile, encrypted) == 0x18, "CArchFile::encrypted");

/* a file read from disk: the ifstream is constructed in place at +0C; the size is taken by seeking to the end,
 * so a missing file only shows up in the constructor's fail check */
struct CFstreamFile : CBaseFile {
    alignas(4) unsigned char stream[0x8C]; /* +0C std::basic_ifstream<char> */

    CFstreamFile(const std::string &path); /* 0x450B20 */
    ~CFstreamFile();                       /* 0x450C90 closes and destroys the stream */
    void *Read(void *buf, unsigned n);     /* 0x450C20 returns the stream reference the read import leaves */
    void *Seek(long pos);                  /* 0x450C30 seekg(pos, beg) */
    void *Advance(long delta);             /* 0x450C50 seekg(delta, cur) */
    int Tell();                            /* 0x450C70 tellg, the position the game's fpos keeps at +0 and +8 */
    void *Destroy(int flags);              /* 0x450D00 the deleting destructor */
};
static_assert(sizeof(CFstreamFile) == 0x98, "CFstreamFile is 0x98 bytes");
static_assert(__builtin_offsetof(CFstreamFile, stream) == 0x0C, "CFstreamFile::stream");
