/* CLuaWrapper: running the game's script files. */
#include "game/common.h"
#include "game/baseentry.h"
#include "game/lua.h"

ORIG_THISCALL(0057D220, void, (void *vm, const char *chunk, int size, const char *name)); /* runs a chunk */

/* The script is loaded from the archive with ".lua" appended and the caller's name is the chunk's name; the file's
 * own name is what the archive lookup and the error message use. */
DECOMP(00432620)
void __thiscall CLuaWrapper::DoFile(const char *fileName)
{
    std::string name(fileName);
    std::string path = name + ".lua";
    alignas(4) unsigned char storage[sizeof(FsBaseFileEntry)];
    FsBaseFileEntry *entry = InitBaseFileEntry((FsBaseFileEntry *)storage, path);
    ORIG_CALL(0057D220)(this, (const char *)entry->data, (int)entry->size, fileName);
    entry->Destroy();
}
