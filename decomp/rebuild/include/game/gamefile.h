/* CGameFile: the whole-file reader the dat loaders use (0x30 bytes, a CGameObject).
 *
 * Open (0x459050) takes the file from the file system into +24, reads it whole into a new buffer at +28 when
 * asked to, and sets +2C; Read (0x458F80) reads into the caller's buffer or (with no buffer) re-reads the whole
 * file into +28, growing it to the requested size when that is not the file's own; Close (0x459010) frees both
 * and clears +2C. The game keeps one instance (0x6CA280) and the loaders open it in turn. */
#pragma once
#include "game/common.h"

/* the file object CFileSystem::OpenFile returns: the virtual table at +00 (deleting dtor, then read), its
 * size at +08 */
struct FsFile {
    void *vftable; /* +00 */
    int unknown04; /* +04 */
    unsigned size; /* +08 */
};

struct CGameFile {
    void *vftable;    /* +00 0x60B71C */
    int objectFlag;   /* +04 the CGameObject flag its base dtor checks */
    std::string name; /* +08 */
    FsFile *file;     /* +24 */
    char *data;       /* +28 the whole file */
    bool opened;      /* +2C */
    CGameFile();      /* 0x459200 */
    ~CGameFile();     /* 0x459170 */
    void Read(void *buf, unsigned n); /* 0x458F80 */
    void Close();                     /* 0x459010 */
};
static_assert(sizeof(CGameFile) == 0x30, "CGameFile is 0x30 bytes");
static_assert(__builtin_offsetof(CGameFile, name) == 0x08, "CGameFile::name");
static_assert(__builtin_offsetof(CGameFile, file) == 0x24, "CGameFile::file");
static_assert(__builtin_offsetof(CGameFile, data) == 0x28, "CGameFile::data");
static_assert(__builtin_offsetof(CGameFile, opened) == 0x2C, "CGameFile::opened");
