/* The folder tree of the file system archive (NSFileSystem).  FileSystemArchive (0x576DD0) is the root folder:
 * every directory of the archive file is an FsFolder, its subdirectories (and files as leaves) hang off it in
 * a std::list<FsFolder>.  CFileSystem owns one archive object (embedded at +0x88) and uses the archive's
 * name -> folder map (the prefixes at +0xB4) to turn a virtual path into a directory outside the paks.
 *
 * The list is laid out as MSVC 8 lays out std::list: a 4-byte empty allocator, the sentinel and the size.  The
 * sentinel is a FsFolderNode whose links form the ring; it has no value.  The list operations take the
 * position/sentinel node explicitly, as the original's library does.
 *
 * The constructors and destructor are spelled out as thiscall helpers (the original's ctor symbols are not
 * distinguishable by name in the build's symbol matching): InitFolder* create a folder in raw storage,
 * CopyFolder copies one into raw storage, DestroyFolder mirrors ~FsFolder.
 */
#pragma once
#include "game/common.h"

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

/* std::length_error("list<T> too long"), thrown by the list size guards of both the folders and the maps */
[[noreturn]] void ThrowFsLengthError(); /* the object is laid out as MSVC 8's std::length_error */
