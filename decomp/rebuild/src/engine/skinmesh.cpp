/* CSkinMesh: lifetime and loading (0x4C06D0 / 0x4C07A0 / 0x4C07C0 / 0x4C0A10).
 *
 * The mesh file is a count of skeleton sub objects, a count of matrix sub objects and a 0x60-byte block.  Each
 * sub object is allocated here and its own constructor (0x4BD0F0 / 0x475720) reads it from the same CGameFile;
 * both kinds end up in the one vector and are later released through their virtual tables.  The vector's insert
 * instantiation stays the original function (0x487860), as do the two sub-object constructors. */
#include "game/skinmesh.h"

ORIG_DATA(00611290); /* CSkinMesh::vftable */
ORIG_DATA(00611294); /* ".\\SkinMesh.cpp" */
ORIG_DATA(006112A4); /* the missing-file message, cp1251 */
ORIG_DATA(0069916C); /* _ThrowInfo of CGameException */

ORIG_THISCALL(00459290, CGameFile *, (CGameFile *self, const std::string *name, int noLoad));
ORIG_THISCALL(004BD0F0, void *, (void *self, CGameFile *file));       /* skeleton sub object */
ORIG_THISCALL(00475720, void *, (void *self, CGameFile *file));       /* matrix sub object */
ORIG_THISCALL(00487860, void, (SkinSubObjectVector *self, SkinSubObject **position, unsigned count,
                               SkinSubObject **value));

inline void *operator new(unsigned int, void *p) { return p; }

typedef void (__thiscall *SkinSubObjectDtor)(void *self, int flags);

/* the sub object goes into the free slot when the vector has one and through its insert otherwise */
static void AppendSubObject(SkinSubObjectVector *vector, SkinSubObject *object)
{
    if (vector->begin == nullptr ||
        (unsigned)(vector->limit - vector->begin) <= (unsigned)(vector->end - vector->begin))
        sub_00487860(vector, vector->end, 1, &object);
    else
        *vector->end++ = object;
}

/* Every sub object is deleted through vtable slot 0; the vector is then erased (the original calls memmove for
 * an empty range) and its buffer freed.  The allocator slot at +04 stays. */
DECOMP(004C06D0)
CSkinMesh::~CSkinMesh()
{
    vftable = d_00611290;

    for (unsigned i = 0; objects.begin != nullptr && i < (unsigned)(objects.end - objects.begin); i++) {
        if (objects.begin[i] != nullptr) {
            ((SkinSubObjectDtor)*(void **)objects.begin[i]->vftable)(objects.begin[i], 1);
            objects.begin[i] = nullptr;
        }
    }

    if (objects.begin)
        operator delete(objects.begin);
    objects.begin = nullptr;
    objects.end = nullptr;
    objects.limit = nullptr;
}

DECOMP(004C07A0)
CSkinMesh *__thiscall DeleteSkinMesh(CSkinMesh *self, unsigned char flags)
{
    self->~CSkinMesh();
    if (flags & 1)
        operator delete(self);
    return self;
}

/* Opens the name (without reading it whole), then the two sub-object lists and the 0x60-byte block.  A missing
 * file becomes a CGameException with the name appended.  The by-value name is the callee's to destroy. */
DECOMP(004C07C0)
void CSkinMesh::Load(Str_4C07C0 name)
{
    alignas(CGameFile) unsigned char fileStorage[sizeof(CGameFile)];
    CGameFile *file = (CGameFile *)fileStorage;
    sub_00459290(file, (const std::string *)&name, 1);

    if (!file->opened) {
        std::string prefix(ORIG_STR(006112A4));
        std::string text = prefix + *(const std::string *)&name;
        CGameException e(text, ORIG_STR(00611294), 0x22);
        _CxxThrowException(&e, d_0069916C);
    }

    unsigned count;
    file->Read(&count, 4);
    for (unsigned i = 0; i < count; i++) {
        SkinSubObject *object = (SkinSubObject *)operator new(0x100);
        if (object)
            sub_004BD0F0(object, file);
        AppendSubObject(&objects, object);
    }

    file->Read(&count, 4);
    for (unsigned i = 0; i < count; i++) {
        SkinSubObject *object = (SkinSubObject *)operator new(0x7C);
        if (object)
            sub_00475720(object, file);
        AppendSubObject(&objects, object);
    }

    file->Read(unknown14, 0x60);

    file->~CGameFile();
    ((std::string *)&name)->~basic_string();
}

/* The constructor tags the mesh, clears the vector and loads the name.  The original deep-copies the by-value
 * name into its own frame for Load and then destroys the caller's copy; the raw storage keeps the local copy
 * from being destroyed twice. */
DECOMP(004C0A10)
CSkinMesh::CSkinMesh(Str_4C07C0 name)
{
    vftable = d_00611290;
    objects.begin = nullptr;
    objects.end = nullptr;
    objects.limit = nullptr;

    alignas(std::string) unsigned char copy[sizeof(std::string)];
    ::new (copy) std::string(*(const std::string *)&name);
    Load(*(Str_4C07C0 *)copy);
    ((std::string *)&name)->~basic_string();
}
