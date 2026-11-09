/* nStd::Object / nStd::BaseEntry and FsBaseFileEntry (see baseentry.h).
 *
 * The destructors reset the vptr to the class they belong to on the way down (FsBaseFileEntry -> BaseEntry ->
 * Object), as the original's do; FsBaseFileEntry's also frees the whole-file buffer before Object checks that the
 * child was detached.  Load resolves a name through FsFileEntry and refuses a miss with "Не найден файл - " and
 * the name. */
#include "game/common.h"
#include "game/fsarchive.h"
#include "game/baseentry.h"

ORIG_DATA(00609288); /* nStd::BaseEntry::vftable */
ORIG_DATA(006092C8); /* FsBaseFileEntry::vftable */
ORIG_DATA(0060925C); /* "Не найден файл - " */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

/* the Object destructor the base entries chain to: the vtable reset and the leftover-child check */
ORIG_THISCALL(00422000, void, (void *object));

DECOMP(004324E0)
nStd::BaseEntry::BaseEntry()
{
    child = nullptr;
    vftable = d_00609288;
    data = nullptr;
    begin = nullptr;
    size = 0;
}

/* The clearers of the template instantiations free the buffer; this base step only resets the vtable and lets
 * Object check the child. */
DECOMP(00432500)
void __thiscall nStd::BaseEntry::Destroy()
{
    vftable = d_00609288;
    sub_00422000(this);
}

DECOMP(00432310)
void __thiscall FsBaseFileEntry::Load(const std::string &fileName)
{
    FsFileEntry file(fileName);
    if (!file.HasName()) {
        std::string msg = ORIG_STR(0060925C) + fileName;
        std::string error(msg);
        _CxxThrowException(&error, d_0069916C);
    }

    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    char *buffer = file.Read();
    data = buffer;
    begin = buffer;
    size = file.size;
    end = buffer + size;
}

DECOMP(004321C0)
char *__thiscall FsBaseFileEntry::LoadFrom(FsFileEntry *file)
{
    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    char *buffer = file->Read();
    data = buffer;
    begin = buffer;
    size = file->size;
    end = buffer + size;
    return buffer;
}

DECOMP(004325A0)
void __thiscall FsBaseFileEntry::Destroy()
{
    vftable = d_006092C8;
    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    vftable = d_00609288;
    sub_00422000(this);
}

DECOMP(004325D0)
void *__thiscall FsBaseFileEntry::Release(unsigned flags)
{
    Destroy();
    if (flags & 1)
        operator delete(this);
    return this;
}

DECOMP(00432540)
FsBaseFileEntry *__thiscall InitBaseFileEntry(FsBaseFileEntry *entry, const std::string &fileName)
{
    entry->child = nullptr;
    entry->vftable = d_006092C8;
    entry->data = nullptr;
    entry->begin = nullptr;
    entry->size = 0;
    entry->Load(fileName);
    return entry;
}

DECOMP(0054F740)
FsBaseFileEntry *__thiscall InitBaseFileEntryFromEntry(FsBaseFileEntry *entry, FsFileEntry *file)
{
    entry->child = nullptr;
    entry->vftable = d_006092C8;
    entry->data = nullptr;
    entry->begin = nullptr;
    entry->size = 0;
    entry->LoadFrom(file);
    return entry;
}
