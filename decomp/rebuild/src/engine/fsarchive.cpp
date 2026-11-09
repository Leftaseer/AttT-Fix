/* FsFolder and FsFolderList: the archive's folder tree and its list - lifetime and depth copy of the list
 * (0x5777F0 / 0x577A90 / 0x5779A0 / 0x577620 / 0x577810 / 0x5787D0) and the folder itself with its children
 * (0x577C60 / 0x577CC0 / 0x577B10 / 0x577A20 / 0x578180 / 0x5788A0 / 0x578A20) and the list size guard
 * (0x470ED0).  These are the game's own instantiations of the file system library's list<FsFolder>; the list
 * node is {next; prev; FsFolder}. */
#include "game/common.h"
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
