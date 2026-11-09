/* CReadInterfaceDat: the table of interface records (0x2C bytes, singleton 0x6C8680).
 *
 * The loader 0x4A71E0 reads the game's interface dat file into a map<string, entry> at +04; the map is the same
 * 0x28-byte engine map CFileSystem uses (FsHashMap): a record is found by its name. */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

struct CReadInterfaceDat {
    void *vftable; /* +00 CSingleton<CReadInterfaceDat> */
    FsHashMap map; /* +04 the loaded records */

    CReadInterfaceDat();                    /* 0x4A7160 */
    ~CReadInterfaceDat();                   /* 0x4A70C0 */
    void Load(const std::string &name);     /* 0x4A71E0 */
};
static_assert(sizeof(CReadInterfaceDat) == 0x2C, "CReadInterfaceDat is 0x2C bytes");
static_assert(__builtin_offsetof(CReadInterfaceDat, map) == 0x04, "CReadInterfaceDat::map");
