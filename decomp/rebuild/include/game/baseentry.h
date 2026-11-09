/* nStd::Object / nStd::BaseEntry: the engine's small owning base classes, and fs::BaseFileEntry<fs::DeleteClearer>
 * (here FsBaseFileEntry): a file entry that loads the whole file into a buffer it owns.
 *
 * Object carries a child (0x422000, src/fixed/f_00422000.c, refuses to die while one is attached); BaseEntry adds
 * the four buffer fields; FsBaseFileEntry fills them from the archive.  The classes keep the original layout and
 * the original vtables (0x607C88 / 0x609288 / 0x6092C8) in a plain vftable field, so the original code can still
 * call their slots - the destructors and the scalar deleting destructor are replaced in place.  The constructors
 * are spelled out as thiscall helpers returning the object in EAX, as the original's callers expect. */
#pragma once
#include "game/common.h"

struct FsFileEntry;

namespace nStd {

struct Object {    /* 0x08 bytes */
    void *vftable; /* +00 */
    Object *child; /* +04 the object must be detached before it dies */
};
static_assert(sizeof(Object) == 0x08, "nStd::Object is 8 bytes");
static_assert(__builtin_offsetof(Object, child) == 0x04, "nStd::Object::child");

struct BaseEntry : Object { /* 0x18 bytes */
    void *data;             /* +08 the owned buffer */
    void *begin;            /* +0C the first byte */
    void *end;              /* +10 one byte past the contents */
    unsigned size;          /* +14 */

    BaseEntry();            /* 0x4324E0 */
    void Destroy();         /* 0x432500 */
};
static_assert(sizeof(BaseEntry) == 0x18, "nStd::BaseEntry is 0x18 bytes");

} // namespace nStd

/* A file entry that owns the file's contents: data and begin are the buffer, end one past its last byte, size its
 * length.  Load throws "Не найден файл - <name>" when the archive has no such file; the destructor frees the
 * buffer before Object's. */
struct FsBaseFileEntry : nStd::BaseEntry {
    void Load(const std::string &fileName);   /* 0x432310 */
    char *LoadFrom(FsFileEntry *file);        /* 0x4321C0 loads a file the caller has already located */
    void Destroy();                           /* 0x4325A0 */
    void *Release(unsigned flags);            /* 0x4325D0 scalar deleting destructor */
};
static_assert(sizeof(FsBaseFileEntry) == 0x18, "FsBaseFileEntry is 0x18 bytes");

/* the constructors; a name the archive doesn't know throws as Load does */
FsBaseFileEntry *__thiscall InitBaseFileEntry(FsBaseFileEntry *entry, const std::string &fileName); /* 0x432540 */
FsBaseFileEntry *__thiscall InitBaseFileEntryFromEntry(FsBaseFileEntry *entry,
                                                       FsFileEntry *file);                          /* 0x54F740 */
