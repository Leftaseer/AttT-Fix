/* The file system archive (fs::FileSystemArchive, 0x11C bytes, singleton 0x6C88D0): the file index of the
 * ResourceN.pak chain and the root of the folder tree.  CFileSystem uses the archive's name -> folder map (the
 * prefixes at +0xB4) to turn a virtual path into a directory outside the paks.
 *
 * The folder tree: every directory of the archive file is an FsFolder, its subdirectories (and files as leaves)
 * hang off it in a std::list<FsFolder>.  Next to the tree the archive keeps a file index: a hash map from a bare
 * file name to the folder the file was found in and its size.  The map's nodes are std::list<FsFileInfo> nodes;
 * the list's primitives are here as well (0x5778D0 / 0x577660 / 0x5778F0 / 0x577910 / 0x577830 / 0x577AB0 /
 * 0x577AD0 / 0x577B80).
 *
 * The list is laid out as MSVC 8 lays out std::list: a 4-byte empty allocator, the sentinel and the size.  The
 * sentinel is a node whose links form the ring; it has no value.  The list operations take the position/sentinel
 * node explicitly, as the original's library does.
 *
 * The constructors and destructor are spelled out as thiscall helpers (the original's ctor symbols are not
 * distinguishable by name in the build's symbol matching): InitFolder* create a folder in raw storage,
 * CopyFolder copies one into raw storage, DestroyFolder mirrors ~FsFolder; the constructors return the object in
 * EAX, as the original's callers expect.
 */
#pragma once
#include "game/common.h"
#include "game/filesystem.h"

struct FsFolder;
struct FsFolderNode;

/* std::list<FsFolder> (0x0C bytes) */
struct FsFolderList {
    unsigned char allocator[4]; /* +00 empty allocator, never read or written */
    FsFolderNode *head;         /* +04 sentinel */
    unsigned size;              /* +08 number of folders */
};

/* a folder of the archive tree (0x2C bytes) */
struct FsFolder {
    std::string name;      /* +00 */
    FsFolderList children; /* +1C */
    FsFolder *parent;      /* +28 */
};

/* one node of the list (0x34 bytes) */
struct FsFolderNode {
    FsFolderNode *next; /* +00 */
    FsFolderNode *prev; /* +04 */
    FsFolder value;     /* +08 */
};

static_assert(sizeof(FsFolderList) == 0x0C, "FsFolderList is 0x0C bytes");
static_assert(__builtin_offsetof(FsFolderList, head) == 0x04, "FsFolderList::head");
static_assert(__builtin_offsetof(FsFolderList, size) == 0x08, "FsFolderList::size");
static_assert(sizeof(FsFolder) == 0x2C, "FsFolder is 0x2C bytes");
static_assert(__builtin_offsetof(FsFolder, children) == 0x1C, "FsFolder::children");
static_assert(__builtin_offsetof(FsFolder, parent) == 0x28, "FsFolder::parent");
static_assert(sizeof(FsFolderNode) == 0x34, "FsFolderNode is 0x34 bytes");
static_assert(__builtin_offsetof(FsFolderNode, value) == 0x08, "FsFolderNode::value");

/* the list; the constructors return the object in EAX, as the original's do */
FsFolderList *__thiscall InitFolderList(FsFolderList *list);                           /* 0x577A90 */
FsFolderList *__thiscall CopyFolderList(FsFolderList *list, const FsFolderList *other); /* 0x5779A0 */
void __thiscall ClearFolderList(FsFolderList *list);                                   /* 0x577620 */
void __thiscall DestroyFolderList(FsFolderList *list);                                 /* 0x577810 */
void __thiscall InsertFolderRange(FsFolderList *list, FsFolderNode *position, FsFolderNode *first,
                                  FsFolderNode *last, const FsFolderList *owner);      /* 0x5787D0 */
void __thiscall AppendFolder(FsFolderList *list, const FsFolder *folder);              /* 0x5788A0 */
void __thiscall AddFolderListSize(FsFolderList *list, unsigned count);                 /* 0x470ED0 */

/* the list's nodes; the sentinel carries no value */
FsFolderNode *__stdcall CreateFolderNodeSentinel();                                    /* 0x5777F0 */
FsFolderNode *__stdcall CreateFolderNode(FsFolderNode *next, FsFolderNode *prev, const FsFolder *folder); /* 0x578180 */

/* the folder; the default one leaves its parent unset, as the original does.  The constructors return the
 * object in EAX, as the MSVC ABI and the original's callers expect */
FsFolder *__thiscall InitFolder(FsFolder *folder);                                     /* 0x577C60 */
FsFolder *__thiscall InitFolderNamed(FsFolder *folder, const std::string *name, FsFolder *parent); /* 0x577CC0 */
FsFolder *__thiscall CopyFolder(FsFolder *folder, const FsFolder *other);              /* 0x577B10 */
void __thiscall DestroyFolder(FsFolder *folder);                                       /* 0x577A20 */
FsFolder *__thiscall AddFolderChild(FsFolder *folder, const std::string *name);        /* 0x578A20 */

/* the archive's file index value (0x24 bytes): a file found on disk, its bare name, the folder it lives in and
 * its size; the folder's name is the directory prefix the index resolves the file to */
struct FsFileInfo {
    std::string name;  /* +00 */
    FsFolder *folder;  /* +1C */
    unsigned size;     /* +20 */
};

/* one node of the index's list (0x2C bytes) */
struct FsFileNode {
    FsFileNode *next; /* +00 */
    FsFileNode *prev; /* +04 */
    FsFileInfo value; /* +08 */
};

/* std::list<FsFileInfo> (0x0C bytes), the same layout as FsFolderList */
struct FsFileList {
    unsigned char allocator[4]; /* +00 */
    FsFileNode *head;           /* +04 sentinel */
    unsigned size;              /* +08 */
};

static_assert(sizeof(FsFileInfo) == 0x24, "FsFileInfo is 0x24 bytes");
static_assert(__builtin_offsetof(FsFileInfo, folder) == 0x1C, "FsFileInfo::folder");
static_assert(__builtin_offsetof(FsFileInfo, size) == 0x20, "FsFileInfo::size");
static_assert(sizeof(FsFileNode) == 0x2C, "FsFileNode is 0x2C bytes");
static_assert(__builtin_offsetof(FsFileNode, value) == 0x08, "FsFileNode::value");
static_assert(sizeof(FsFileList) == 0x0C, "FsFileList is 0x0C bytes");
static_assert(__builtin_offsetof(FsFileList, head) == 0x04, "FsFileList::head");
static_assert(__builtin_offsetof(FsFileList, size) == 0x08, "FsFileList::size");

/* the index's nodes and list: the value copier, the node factory, the size guard and the list's insertions.
 * The list constructor 0x577AB0 stays the original (see fsarchive.cpp: its prototype data is inconsistent). */
void __cdecl CopyFileInfo(FsFileInfo *info, const FsFileInfo *other);                      /* 0x577660 */
void __stdcall ConstructFileInfo(FsFileInfo *info, const FsFileInfo *other);               /* 0x5778F0 */
void __thiscall AddFileListSize(FsFileList *list, unsigned count);                         /* 0x577830 */
FsFileNode *__stdcall CreateFileNode(FsFileNode *next, FsFileNode *prev, const FsFileInfo *info); /* 0x577910 */
FsFileNode *__stdcall CreateFileNodeSentinel();                                            /* 0x5778D0 */
void __thiscall InsertFile(FsFileList *list, FsFileNode *position, const FsFileInfo *info); /* 0x577AD0 */
void __thiscall InsertFileRange(FsFileList *list, FsFileNode *position, FsFileNode *first,
                                FsFileNode *last, const void *allocator);                  /* 0x577B80 */

/* std::length_error("list<T> too long"), thrown by the list size guards of both the folders and the maps */
[[noreturn]] void ThrowFsLengthError(); /* the object is laid out as MSVC 8's std::length_error */

/* The archive singleton.  Its ctor opens Resource.pak next to the exe for its size, copies CFileSystem's whole
 * pak directory into +38, then walks the ResourceN.pak chain for as long as it opens: every pak's signature,
 * version and directory are read, version 200 paks are decrypted and every record goes into +38.  +10 keeps the
 * name -> folder index the file system's path resolution uses. */
struct FileSystemArchive {
    void *vftable;             /* +00 fs::FileSystemArchive::vftable, 0x6C88D0 owns the object */
    int pakVersion;            /* +04 200 = the encrypted header and directory */
    unsigned pakCount;         /* +08 records in the last pak read */
    unsigned char unused0C[4]; /* +0C XORed with the key on version 200, never read */
    FsHashMap nameIndex;       /* +10 map<string, FsFileInfo> (0x2C-byte nodes) */
    FsHashMap files;           /* +38 map<string, PakEntry> (0x30-byte nodes) */
    void *pakHandle;           /* +60 the Resource.pak handle, -1 once closed */
    std::ifstream stream;      /* +64 the stream of the ResourceN.pak being read */
    FsFolder root;             /* +F0 the folder tree */
};
static_assert(sizeof(FileSystemArchive) == 0x11C, "FileSystemArchive is 0x11C bytes");
static_assert(__builtin_offsetof(FileSystemArchive, pakVersion) == 0x04, "FileSystemArchive::pakVersion");
static_assert(__builtin_offsetof(FileSystemArchive, pakCount) == 0x08, "FileSystemArchive::pakCount");
static_assert(__builtin_offsetof(FileSystemArchive, nameIndex) == 0x10, "FileSystemArchive::nameIndex");
static_assert(__builtin_offsetof(FileSystemArchive, files) == 0x38, "FileSystemArchive::files");
static_assert(__builtin_offsetof(FileSystemArchive, pakHandle) == 0x60, "FileSystemArchive::pakHandle");
static_assert(__builtin_offsetof(FileSystemArchive, stream) == 0x64, "FileSystemArchive::stream");
static_assert(__builtin_offsetof(FileSystemArchive, root) == 0xF0, "FileSystemArchive::root");

/* "%d" through the shared sprintf buffer, as a string */
std::string IntToString(int value); /* 0x576720 */

/* where a name lives: the pak section of a pak entry, or offset 0 and the size of a file on disk */
struct FsFileLocation {
    unsigned offset; /* +00 */
    unsigned size;   /* +04 */
    int pak;         /* +08 */
};

/* A name with a drive is a disk path and only its size is reported; any other name is looked up (lowercased)
 * in the archive's file map.  An unknown name yields a zero location. */
FsFileLocation *__thiscall LocateArchiveFile(FileSystemArchive *archive, FsFileLocation *out,
                                             const std::string *name); /* 0x576A90 */

/* An archive file entry (0x28 bytes): where a name lives plus the name itself.  A name the archive does not know
 * is recorded with an empty name, and Read refuses it.  Read loads the whole file: from the ResourceN.pak named
 * in the entry, or - when the name carries a drive - straight from disk. */
struct FsFileEntry {
    unsigned size;    /* +00 */
    unsigned offset;  /* +04 */
    std::string name; /* +08 */
    int pak;          /* +24 */

    FsFileEntry(const std::string &fileName); /* 0x432200 */
    void Locate(const std::string &fileName); /* 0x432010 */
    bool HasName() const;                     /* 0x432070 whether the archive knows the name */
    char *Read();                             /* 0x576820 */
};
static_assert(sizeof(FsFileEntry) == 0x28, "FsFileEntry is 0x28 bytes");
static_assert(__builtin_offsetof(FsFileEntry, offset) == 0x04, "FsFileEntry::offset");
static_assert(__builtin_offsetof(FsFileEntry, name) == 0x08, "FsFileEntry::name");
static_assert(__builtin_offsetof(FsFileEntry, pak) == 0x24, "FsFileEntry::pak");

/* the singleton's lifetime and the object it builds; the ctor and the creator return the object in EAX */
FileSystemArchive *__thiscall InitFileSystemArchive(FileSystemArchive *archive);      /* 0x576DD0 */
void __thiscall DestroyFileSystemArchive(FileSystemArchive *archive);                 /* 0x576C90 */
void *__thiscall DeleteFileSystemArchive(FileSystemArchive *archive, unsigned flags); /* 0x576DB0 */
FileSystemArchive *__cdecl CreateFileSystemArchive();                                 /* 0x44AB70 */
