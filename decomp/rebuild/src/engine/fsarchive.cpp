/* FsFolder and FsFolderList: the archive's folder tree and its list - lifetime and depth copy of the list
 * (0x5777F0 / 0x577A90 / 0x5779A0 / 0x577620 / 0x577810 / 0x5787D0) and the folder itself with its children
 * (0x577C60 / 0x577CC0 / 0x577B10 / 0x577A20 / 0x578180 / 0x5788A0 / 0x578A20) and the list size guard
 * (0x470ED0).  These are the game's own instantiations of the file system library's list<FsFolder>; the list
 * node is {next; prev; FsFolder}.
 *
 * The archive's file index uses the same machinery for std::list<FsFileInfo>: the value copier (0x577660), its
 * stdcall thunk (0x5778F0), the sentinel (0x5778D0), the node factory (0x577910), the size guard (0x577830)
 * and the insertions (0x577AD0 / 0x577B80).  The node is {next; prev; FsFileInfo}.
 *
 * Finally the archive itself (0x576DD0 and its lifetime): IntToString, the pak chain reader of the ctor, the
 * destructor and the singleton creator, plus the archive's file entry (0x432200 / 0x432010 / 0x576820): the
 * ctor, the locator fill and the whole-file reader. */
#include "game/common.h"
#include "game/globals.h"
#include "game/config.h"
#include "game/fsarchive.h"

ORIG_DATA(00607CCC); /* "list<T> too long" */
ORIG_DATA(00607B18); /* std::length_error vftable */
ORIG_DATA(00607B24); /* the vftable the thrown object ends up with */
ORIG_DATA(00699050); /* std::length_error _ThrowInfo */

DECOMP_C void (__thiscall *imp_006073A4)(void *) __asm__("__imp_??0exception@std@@QAE@XZ");

inline void *operator new(unsigned int, void *p) { return p; }

/* the length_error the list and map size guards throw: vftable, std::exception's what/dofree and the message */
struct FsLengthError {
    void *vftable;       /* +00 */
    const char *what;    /* +04 */
    int doFree;          /* +08 */
    std::string message; /* +0C */
};

void ThrowFsLengthError()
{
    FsLengthError error;
    imp_006073A4(&error);
    error.vftable = d_00607B18;
    new (&error.message) std::string(ORIG_STR(00607CCC));
    error.vftable = d_00607B24;
    _CxxThrowException(&error, d_00699050);
    __builtin_unreachable();
}

/* The sentinel of a folder list: a bare 0x34-byte node whose links point at itself.  It never carries a
 * value, so the list code never constructs or destroys it. */
DECOMP(005777F0)
FsFolderNode *__stdcall CreateFolderNodeSentinel()
{
    FsFolderNode *node = (FsFolderNode *)operator new(sizeof(FsFolderNode));
    node->next = node;
    node->prev = node;
    return node;
}

DECOMP(00577A90)
FsFolderList *__thiscall InitFolderList(FsFolderList *list)
{
    list->head = CreateFolderNodeSentinel();
    list->size = 0;
    return list;
}

/* A deep copy: a fresh sentinel, then every node of the source range copied before the new head. */
DECOMP(005779A0)
FsFolderList *__thiscall CopyFolderList(FsFolderList *list, const FsFolderList *other)
{
    list->head = CreateFolderNodeSentinel();
    list->size = 0;
    InsertFolderRange(list, list->head, other->head->next, other->head, other);
    return list;
}

/* Empties the ring, destroying every folder in it; the sentinel itself stays. */
DECOMP(00577620)
void __thiscall ClearFolderList(FsFolderList *list)
{
    FsFolderNode *sentinel = list->head;
    FsFolderNode *node = sentinel->next;
    sentinel->next = sentinel;
    sentinel->prev = sentinel;
    list->size = 0;
    while (node != sentinel) {
        FsFolderNode *next = node->next;
        DestroyFolder(&node->value);
        operator delete(node);
        node = next;
    }
}

/* Clear() and the sentinel goes too: the list is unusable afterwards, as the folder destructor wants it. */
DECOMP(00577810)
void __thiscall DestroyFolderList(FsFolderList *list)
{
    ClearFolderList(list);
    operator delete(list->head);
    list->head = nullptr;
}

/* Copies the [first, last) range of another list before position (the sentinel in every caller).  The fourth
 * argument is the allocator of the library's insert, which the original never reads. */
DECOMP(005787D0)
void __thiscall InsertFolderRange(FsFolderList *list, FsFolderNode *position, FsFolderNode *first,
                                  FsFolderNode *last, const FsFolderList *owner)
{
    (void)owner;
    for (FsFolderNode *node = first; node != last; node = node->next) {
        FsFolderNode *created = CreateFolderNode(position, position->prev, &node->value);
        AddFolderListSize(list, 1);
        position->prev = created;
        created->prev->next = created;
    }
}

DECOMP(005788A0)
void __thiscall AppendFolder(FsFolderList *list, const FsFolder *folder)
{
    FsFolderNode *created = CreateFolderNode(list->head, list->head->prev, folder);
    AddFolderListSize(list, 1);
    list->head->prev = created;
    created->prev->next = created;
}

/* The list size guard: std::list<FsFolder>'s max_size is 0xFFFFFFFF / sizeof(FsFolder); growing past it
 * throws. */
DECOMP(00470ED0)
void __thiscall AddFolderListSize(FsFolderList *list, unsigned count)
{
    if (0x5D1745Du - list->size < count)
        ThrowFsLengthError();
    list->size += count;
}

/* The node factory: allocate, link, copy the folder value. */
DECOMP(00578180)
FsFolderNode *__stdcall CreateFolderNode(FsFolderNode *next, FsFolderNode *prev, const FsFolder *folder)
{
    FsFolderNode *node = (FsFolderNode *)operator new(sizeof(FsFolderNode));
    node->next = next;
    node->prev = prev;
    CopyFolder(&node->value, folder);
    return node;
}

/* The default folder leaves its parent unset (the original does not write it). */
DECOMP(00577C60)
FsFolder *__thiscall InitFolder(FsFolder *folder)
{
    new (&folder->name) std::string();
    InitFolderList(&folder->children);
    return folder;
}

DECOMP(00577CC0)
FsFolder *__thiscall InitFolderNamed(FsFolder *folder, const std::string *name, FsFolder *parent)
{
    new (&folder->name) std::string(*name);
    InitFolderList(&folder->children);
    folder->parent = parent;
    return folder;
}

DECOMP(00577B10)
FsFolder *__thiscall CopyFolder(FsFolder *folder, const FsFolder *other)
{
    new (&folder->name) std::string(other->name);
    CopyFolderList(&folder->children, &other->children);
    folder->parent = other->parent;
    return folder;
}

/* Tear down the children deepest first, then the name string. */
DECOMP(00577A20)
void __thiscall DestroyFolder(FsFolder *folder)
{
    DestroyFolderList(&folder->children);
    folder->name.~basic_string();
}

/* The file index's value: a bare file name, the folder it was found in and its size.  The helper constructs
 * the value in raw storage; it is the copy constructor of the node factory and of the range insertion. */
DECOMP(00577660)
void __cdecl CopyFileInfo(FsFileInfo *info, const FsFileInfo *other)
{
    if (!info)
        return;
    new (&info->name) std::string(other->name);
    info->folder = other->folder;
    info->size = other->size;
}

/* The stdcall thunk of the value copier (the node factory calls it in the original). */
DECOMP(005778F0)
void __stdcall ConstructFileInfo(FsFileInfo *info, const FsFileInfo *other)
{
    CopyFileInfo(info, other);
}

/* The sentinel of a file list: a bare 0x2C-byte node whose links point at itself. */
DECOMP(005778D0)
FsFileNode *__stdcall CreateFileNodeSentinel()
{
    FsFileNode *node = (FsFileNode *)operator new(sizeof(FsFileNode));
    node->next = node;
    node->prev = node;
    return node;
}

/* The node factory: allocate, link, copy the value. */
DECOMP(00577910)
FsFileNode *__stdcall CreateFileNode(FsFileNode *next, FsFileNode *prev, const FsFileInfo *info)
{
    FsFileNode *node = (FsFileNode *)operator new(sizeof(FsFileNode));
    node->next = next;
    node->prev = prev;
    CopyFileInfo(&node->value, info);
    return node;
}

/* The list size guard: std::list<FsFileInfo>'s max_size is 0xFFFFFFFF / sizeof(FsFileInfo); growing past it
 * throws. */
DECOMP(00577830)
void __thiscall AddFileListSize(FsFileList *list, unsigned count)
{
    if (0x71C71C7u - list->size < count)
        ThrowFsLengthError();
    list->size += count;
}

/* 0x577AB0 (the list constructor: a fresh sentinel, size 0, this in EAX) stays the original: the generated
 * prototype records a second register parameter that the machine code does not read (convs.tsv), so build.py
 * cannot pair the hand-written declaration with it.  The function has no references in the image. */

/* Links a new node before position. */
DECOMP(00577AD0)
void __thiscall InsertFile(FsFileList *list, FsFileNode *position, const FsFileInfo *info)
{
    FsFileNode *created = CreateFileNode(position, position->prev, info);
    AddFileListSize(list, 1);
    position->prev = created;
    created->prev->next = created;
}

/* Copies the [first, last) range of another list before position (the sentinel in every caller); the allocator
 * of the library's insert is never read. */
DECOMP(00577B80)
void __thiscall InsertFileRange(FsFileList *list, FsFileNode *position, FsFileNode *first,
                                FsFileNode *last, const void *allocator)
{
    (void)allocator;
    for (FsFileNode *node = first; node != last; node = node->next) {
        FsFileNode *created = CreateFileNode(position, position->prev, &node->value);
        AddFileListSize(list, 1);
        position->prev = created;
        created->prev->next = created;
    }
}

/* Creates the subfolder from a temporary {name; empty children; this} and returns it in the list. */
DECOMP(00578A20)
FsFolder *__thiscall AddFolderChild(FsFolder *folder, const std::string *name)
{
    alignas(4) unsigned char storage[sizeof(FsFolder)];
    FsFolder *temporary = (FsFolder *)storage;
    InitFolderNamed(temporary, name, folder);
    FsFolderNode *node = CreateFolderNode(folder->children.head, folder->children.head->prev, temporary);
    AddFolderListSize(&folder->children, 1);
    folder->children.head->prev = node;
    node->prev->next = node;
    DestroyFolder(temporary);
    return &folder->children.head->prev->value;
}

/* ---------------------------------------------------------------------------------------------------------------
 * fs::FileSystemArchive: the archive singleton (0x11C bytes) the file system resolves paths and pak entries
 * through.  IntToString (0x576720), the ctor (0x576DD0), the destructor (0x576C90), its deleting twin
 * (0x576DB0) and the singleton creator (0x44AB70). */

ORIG_DATA(0061D828); /* fs::FileSystemArchive::vftable (the deleting dtor is its first entry) */
ORIG_DATA(0061D7E4); /* Singleton<fs::FileSystemArchive>::vftable, written by the dtor */
ORIG_DATA(0061D82C); /* ".\\new\\FileSystemArchive.cpp" */
ORIG_DATA(0060B0F4); /* "Resource.pak" */
ORIG_DATA(0060B218); /* "Resource" */
ORIG_DATA(0060B224); /* ".pak" */
ORIG_DATA(0060B1AC); /* "Сигнатура архивного файла не совпадает с требуемой " */
ORIG_DATA(0060B1F4); /* "Не удается открыть файл - " */
ORIG_DATA(006C7BD8); /* the 16-byte key of the version 200 paks */
ORIG_DATA(006C88D0); /* the archive singleton */
ORIG_DATA(008D10A8); /* the sprintf buffer of IntToString */
ORIG_DATA(0069916C); /* CGameException _ThrowInfo */

ORIG_THISCALL(004CCC80, void, (void *vector, unsigned count, const void *value)); /* fill a vector with copies */
ORIG_THISCALL(00452760, void *, (void *self, void *out));                        /* CFileSystem::GetFiles */
ORIG_THISCALL(00451CF0, void *, (void *self, const void *other));                /* map<string,PakEntry>::operator= */
ORIG_FN(005E3B10, void *, (unsigned int size));                                  /* operator new[] */

/* The original passes the entry to InsertName by value: the caller builds the entry, then the argument copy of
 * it, so three strings exist before the node's own copy.  The allocation pattern is part of the behaviour. */
static void InsertPakEntry(FsHashMap *files, const char *name, unsigned offset, unsigned size, int pak)
{
    std::string fileName(name);
    alignas(4) unsigned char entryStorage[sizeof(PakEntry)];
    PakEntry *entry = (PakEntry *)entryStorage;
    new (&entry->name) std::string(fileName);
    entry->offset = offset;
    entry->size = size;
    entry->pak = pak;
    alignas(4) unsigned char argumentStorage[sizeof(PakEntry)];
    PakEntry *argument = (PakEntry *)argumentStorage;
    new (&argument->name) std::string(entry->name);
    argument->offset = offset;
    argument->size = size;
    argument->pak = pak;
    FsInsertResult result;
    files->InsertName(&result, argument);
    argument->name.~basic_string();
    entry->name.~basic_string();
}

static void ThrowArchiveError(const std::string &msg, int line)
{
    CGameException error(msg, ORIG_STR(0061D82C), line);
    _CxxThrowException(&error, d_0069916C);
    __builtin_unreachable();
}

/* "%d" through one shared buffer.  The string is returned through the caller's hidden pointer, as MSVC does. */
DECOMP(00576720)
std::string IntToString(int value)
{
    sprintf(d_008D10A8, "%d", value);
    return std::string(d_008D10A8);
}

/* Locates a name: a drive letter makes it a file on disk (its size is measured by seeking to the end), any
 * other name is looked up in the pak directory map under its lowercased spelling. */
DECOMP(00576A90)
FsFileLocation *__thiscall LocateArchiveFile(FileSystemArchive *archive, FsFileLocation *out,
                                             const std::string *name)
{
    if (name->find(':', 0) == std::string::npos) {
        std::string key(CharLowerA(const_cast<char *>(name->c_str())));
        FsStringNode *node;
        archive->files.FindName(&node, &key);
        if (node == (FsStringNode *)archive->files.sentinel) {
            out->offset = 0;
            out->size = 0;
            out->pak = 0;
        } else {
            const unsigned *value = (const unsigned *)((char *)node + 0x24);
            out->offset = value[0];
            out->size = value[1];
            out->pak = (int)value[2];
        }
    } else {
        std::string path(*name);
        std::ifstream stream(path.c_str(), std::ios_base::_In | std::ios_base::_Binary, std::ios_base::_Openprot);
        stream.seekg(0, 2);
        std::fpos_int pos = stream.tellg();
        stream.seekg(0, 0);
        out->offset = 0;
        out->size = pos.state0 + pos.pos;
        out->pak = 0;
    }
    return out;
}

/* ---------------------------------------------------------------------------------------------------------------
 * FsFileEntry: one file of the archive.  The ctor (0x432200) caches the archive singleton in 0x8D10A4 and fills
 * the entry through it (0x432010); Read (0x576820) loads the whole contents. */

ORIG_DATA(008D10A4); /* the archive singleton the entry consults */
ORIG_DATA(0060FA8B); /* "" - the name an entry the archive doesn't know ends up with */
ORIG_DATA(0061D7FC); /* "Попытка прочитать несуществующий файл" */

DECOMP(00432200)
FsFileEntry::FsFileEntry(const std::string &fileName) : name()
{
    ORIG_VAR(008D10A4, void *) = ORIG_VAR(006C88D0, void *);
    Locate(fileName);
}

/* Fills the entry from the archive's file map; a name it doesn't know has size 0 and loses its name. */
DECOMP(00432010)
void __thiscall FsFileEntry::Locate(const std::string &fileName)
{
    FsFileLocation location;
    LocateArchiveFile((FileSystemArchive *)ORIG_VAR(008D10A4, void *), &location, &fileName);
    size = location.size;
    offset = location.offset;
    name = fileName;
    pak = location.pak;
    if (size == 0)
        name = ORIG_STR(0060FA8B);
}

/* Whether the archive gave the entry a name: a name it didn't know was cleared in Locate. */
DECOMP(00432070)
bool __thiscall FsFileEntry::HasName() const
{
    return !name.empty();
}

/* Reads the whole file into a new buffer.  A name with a drive is opened as is, any other name through the
 * ResourceN.pak it was found in; the buffer gets one terminating zero past the size.  The path is then replaced
 * with the opened-files log (a debug leftover of the original; the assignment never takes effect). */
DECOMP(00576820)
char *__thiscall FsFileEntry::Read()
{
    if (name.empty()) {
        std::string msg(ORIG_STR(0061D7FC));
        std::string error(msg);
        _CxxThrowException(&error, d_0069916C);
    }

    char *data = (char *)sub_005E3B10(size + 1);
    std::string path;
    if (name.find(':', 0) == std::string::npos) {
        std::string digits = IntToString(pak);
        path = ((nCfg::GamePath *)g_gamePath)->exePath + "Resource" + digits + ".pak";
    } else {
        path = name;
    }

    std::ifstream stream(path.c_str(), std::ios_base::_In | std::ios_base::_Binary, std::ios_base::_Openprot);
    std::fpos_int pos = {offset, 0, 0, 0, 0, 0};
    stream.seekg(pos);
    stream.read(data, (int)size);
    stream.close();
    path = ((nCfg::GamePath *)g_gamePath)->exePath + "opened_files.log";
    data[size] = 0;
    return data;
}

/* The ctor: the two maps, the embedded stream and the folder tree, then the ResourceN.pak chain.  Resource.pak
 * next to the exe is opened only for its size (its handle is kept), and the chain replaces the archive's copy of
 * CFileSystem's pak directory with the records of every pak that opens.  The original hands InitStringMap the
 * address of an uninitialised stack byte for the empty allocator; nothing ever reads the value. */
DECOMP(00576DD0)
FileSystemArchive *__thiscall InitFileSystemArchive(FileSystemArchive *archive)
{
    unsigned char allocator = 0;

    archive->vftable = d_0061D828;

    /* the name -> folder index map; the original's map init (0x576C20) is inlined here because its recorded
     * convention disagrees with the machine code, so build.py cannot pair a hand-written copy with it */
    archive->nameIndex.sentinel = CreateFileNodeSentinel();
    archive->nameIndex.size = 0;
    {
        void *sentinel = archive->nameIndex.sentinel;
        sub_004CCC80(&archive->nameIndex.vectorAlloc, 9, &sentinel);
    }
    archive->nameIndex.mask = 1;
    archive->nameIndex.count = 1;

    archive->files.InitStringMap(allocator, &allocator);
    new (&archive->stream) std::ifstream();
    InitFolder(&archive->root);

    nCfg::GamePath *gamePath = (nCfg::GamePath *)g_gamePath;
    std::string path = gamePath->exePath + "Resource.pak";
    archive->pakHandle = CreateFileA(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                                     OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    GetFileSize(archive->pakHandle, nullptr);

    /* the archive starts from the file system's own directory of all opened paks */
    FsHashMap filesCopy;
    sub_00452760(CFileSystem::Instance(), &filesCopy);
    if (&archive->files != &filesCopy)
        sub_00451CF0(&archive->files, &filesCopy);
    if (filesCopy.begin)
        operator delete(filesCopy.begin);
    filesCopy.begin = nullptr;
    filesCopy.end = nullptr;
    filesCopy.limit = nullptr;
    ClearStringNodeList((char *)&filesCopy + 4);
    operator delete(filesCopy.sentinel);

    if (archive->files.size == 0) {
        unsigned i = 0;
        for (;; i++) {
            std::string digits = IntToString((int)i);
            path = gamePath->exePath + "Resource" + digits + ".pak";
            archive->stream.open(path.c_str(), std::ios_base::_In | std::ios_base::_Binary,
                                 std::ios_base::_Openprot);
            if (archive->stream.fail())
                break;

            char header[12];
            archive->stream.read(header, sizeof header);
            if (header[0] != 'G' || header[1] != 'R' || header[2] != 'E' || header[3] != 'S') {
                archive->stream.close();
                ThrowArchiveError(std::string(ORIG_STR(0060B1AC)), 0x46);
            }
            archive->pakVersion = *(int *)(header + 4);
            archive->pakCount = *(unsigned *)(header + 8);
            unsigned char *key = (unsigned char *)d_006C7BD8;
            if (archive->pakVersion == 200) {
                /* the four bytes at +0C are part of the encrypted header; nothing ever reads them */
                for (int j = 0; j < 4; j++)
                    archive->unused0C[j] ^= key[j];
                for (int j = 0; j < 4; j++)
                    ((unsigned char *)&archive->pakCount)[j] ^= key[4 + j];
            }

            /* new[] gets the size saturated on 32-bit overflow; the read and the decrypt loop use the wrapped one */
            unsigned size = archive->pakCount * 0x88;
            unsigned long long bytes = (unsigned long long)archive->pakCount * 0x88;
            PakRecord *records = (PakRecord *)sub_005E3B10((unsigned)(bytes >> 32) ? 0xFFFFFFFFu : size);
            archive->stream.read((char *)records, size);
            if (archive->pakVersion == 200)
                for (unsigned j = 0; j < size; j++)
                    ((unsigned char *)records)[j] ^= key[j % 16];

            for (unsigned k = 0; k < archive->pakCount; k++) {
                const PakRecord *record = &records[k];
                if (i == 0) {
                    InsertPakEntry(&archive->files, record->name, record->offset, record->size, (int)i);
                } else {
                    std::string keyName(record->name);
                    FsStringNode *node;
                    archive->files.FindName(&node, &keyName);
                    keyName.~basic_string();
                    if (node == (FsStringNode *)archive->files.sentinel) {
                        InsertPakEntry(&archive->files, record->name, record->offset, record->size, (int)i);
                    } else {
                        /* a later pak overrides the record of an earlier one */
                        unsigned *value = (unsigned *)((char *)node + 0x24);
                        value[0] = record->offset;
                        value[1] = record->size;
                        value[2] = i;
                    }
                }
            }
            operator delete[](records);
            archive->stream.close();
        }

        if (i == 0)
            ThrowArchiveError(ORIG_STR(0060B1F4) + path, 0x38);
    }
    return archive;
}

DECOMP(00576C90)
void __thiscall DestroyFileSystemArchive(FileSystemArchive *archive)
{
    archive->vftable = d_0061D828;
    CloseHandle(archive->pakHandle);
    archive->pakHandle = (void *)-1;
    DestroyFolder(&archive->root);
    archive->stream.~basic_ifstream();

    if (archive->files.begin)
        operator delete(archive->files.begin);
    archive->files.begin = nullptr;
    archive->files.end = nullptr;
    archive->files.limit = nullptr;
    ClearStringNodeList((char *)&archive->files + 4);
    operator delete(archive->files.sentinel);
    archive->files.sentinel = nullptr;

    if (archive->nameIndex.begin)
        operator delete(archive->nameIndex.begin);
    archive->nameIndex.begin = nullptr;
    archive->nameIndex.end = nullptr;
    archive->nameIndex.limit = nullptr;
    ClearStringNodeList((char *)&archive->nameIndex + 4);
    operator delete(archive->nameIndex.sentinel);
    archive->nameIndex.sentinel = nullptr;

    archive->vftable = d_0061D7E4;
}

DECOMP(00576DB0)
void *__thiscall DeleteFileSystemArchive(FileSystemArchive *archive, unsigned flags)
{
    DestroyFileSystemArchive(archive);
    if (flags & 1)
        operator delete(archive);
    return archive;
}

DECOMP(0044AB70)
FileSystemArchive *__cdecl CreateFileSystemArchive()
{
    void *memory = operator new(sizeof(FileSystemArchive));
    if (memory)
        memory = InitFileSystemArchive((FileSystemArchive *)memory);
    ORIG_VAR(006C88D0, void *) = memory;
    return (FileSystemArchive *)memory;
}
