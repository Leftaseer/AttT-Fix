/* CGameFile: the whole-file reader and its lifetime (0x459200 / 0x459170 / 0x459050 / 0x458F80 / 0x459010). */
#include "game/common.h"
#include "game/gamefile.h"
#include "game/filesystem.h"

ORIG_DATA(0060B71C); /* CGameFile::vftable */
ORIG_DATA(006C8DE0); /* number of live CGameFile readers */
ORIG_DATA(006C8DE4); /* the file system the readers open through */

ORIG_FN(005E3B10, void *, (unsigned int size));       /* operator new[] */

inline void *operator new(unsigned int, void *p) { return p; }

typedef void (__thiscall *FsFileDtor)(FsFile *self, int flags);
typedef void (__thiscall *FsFileRead)(FsFile *self, void *buf, unsigned n);

static void ReadFsFile(FsFile *file, void *buf, unsigned n)
{
    ((FsFileRead)(*(void ***)file)[1])(file, buf, n);
}

DECOMP(00459200)
CGameFile::CGameFile() : name()
{
    vftable = d_0060B71C;
    owner = nullptr;
    file = nullptr;
    data = nullptr;
    opened = false;
    if (ORIG_VAR(006C8DE0, int) == 0)
        ORIG_VAR(006C8DE4, void *) = CFileSystem::Instance();
    ORIG_VAR(006C8DE0, int)++;
}

/* the original destroys name before the CGameObject base; the member destruction here follows the body, so only
 * the final state matches (the base dtor leaves its own vtable, as in the original) */
DECOMP(00459170)
CGameFile::~CGameFile()
{
    vftable = d_0060B71C;
    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    if (file) {
        ((FsFileDtor)(*(void ***)file)[0])(file, 1);
        file = nullptr;
    }
    opened = false;
    ORIG_VAR(006C8DE0, int)--;
}

/* no buffer: keep the whole file in data, sized to the file (with its ending NUL) unless another size was asked
 * for, in which case the buffer is reallocated; with a buffer the file is read straight into it */
DECOMP(00458F80)
void CGameFile::Read(void *buf, unsigned n)
{
    if (buf) {
        ReadFsFile(file, buf, n);
        return;
    }
    if (n != 0 && n != file->size) {
        if (data) {
            operator delete(data); /* the original uses scalar delete here and delete[] elsewhere */
            data = nullptr;
        }
        data = (char *)sub_005E3B10(n);
    } else if (!data) {
        n = file->size;
        data = (char *)sub_005E3B10(n + 1);
        data[n] = '\0';
    }
    ReadFsFile(file, data, n);
}

/* opens the named file: the old data and stream go first, then the name is kept and the stream opened; a missing
 * file raises 0xE0000002 with a new string of the name (and 0x3C as the argument count, as the original has it)
 * and returns false; otherwise the reader is marked open and, unless asked not to, the file is read whole into a
 * new buffer of its size with a terminating NUL */
DECOMP(00459050)
bool CGameFile::Open(const std::string &fileName, int noLoad)
{
    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    if (file) {
        ((FsFileDtor)(*(void ***)file)[0])(file, 1);
        file = nullptr;
    }
    opened = false;
    name = fileName;

    file = (FsFile *)static_cast<CFileSystem *>(ORIG_VAR(006C8DE4, void *))->OpenFile(fileName);
    if (!file) {
        void *str = operator new(sizeof(std::string));
        if (str)
            str = ::new (str) std::string(fileName.c_str());
        ULONG_PTR args[15];
        args[0] = (ULONG_PTR)str;
        opened = false;
        RaiseException(0xE0000002, 0, 0x3C, args);
        return false;
    }
    opened = true;
    if (!noLoad) {
        unsigned n = 0;
        if (!data) {
            n = file->size;
            data = (char *)sub_005E3B10(n + 1);
            data[n] = '\0';
        }
        ReadFsFile(file, data, n);
    }
    return true;
}

DECOMP(00459010)
void CGameFile::Close()
{
    if (data) {
        operator delete[](data);
        data = nullptr;
    }
    if (file) {
        ((FsFileDtor)(*(void ***)file)[0])(file, 1);
        file = nullptr;
    }
    opened = false;
}
