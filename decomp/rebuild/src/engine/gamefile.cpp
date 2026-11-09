/* CGameFile: the whole-file reader and its lifetime (0x459200 / 0x459170 / 0x458F80 / 0x459010). */
#include "game/common.h"
#include "game/gamefile.h"

ORIG_DATA(0060B71C); /* CGameFile::vftable */
ORIG_DATA(006C8DE0); /* number of live CGameFile readers */
ORIG_DATA(006C8DE4); /* the file system the readers open through */

ORIG_FN(0044ABE0, void *, ());                        /* creates the file system on first use */
ORIG_FN(005E3B10, void *, (unsigned int size));       /* operator new[] */
ORIG_THISCALL(00424C70, void, (void *self));          /* CGameObject::~CGameObject */

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
    objectFlag = 0;
    file = nullptr;
    data = nullptr;
    opened = false;
    if (ORIG_VAR(006C8DE0, int) == 0)
        ORIG_VAR(006C8DE4, void *) = sub_0044ABE0();
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
    sub_00424C70(this);
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
