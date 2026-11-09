/* CSkinMesh: lifetime and loading (0x4C06D0 / 0x4C07A0 / 0x4C07C0 / 0x4C0A10) and the draw path that walks
 * the sub objects (0x4C0620 / 0x4C0680); SkinMeshObject: its animation state (0x4C0B20 / 0x4C0BF0) and the four
 * draw entry points (0x4C0DE0 / 0x4C0E30 / 0x4C0E60 / 0x4C0EA0).
 *
 * The mesh file is a count of skeleton sub objects, a count of matrix sub objects and a 0x60-byte block.  Each
 * sub object is allocated here and its own constructor (0x4BD0F0 / 0x475720) reads it from the same CGameFile;
 * both kinds end up in the one vector and are later released through their virtual tables.  The vector's insert
 * instantiation stays the original function (0x487860), as do the two sub-object constructors.
 *
 * The draw helpers call every sub object through its own virtual table with the object's animation group, the
 * frame and - for the four-argument variant - the mesh's entry of the draw table; the wrappers pick the mesh
 * (clamped, or the current one) and the two-argument helpers that only need three arguments go through another
 * virtual slot.  The two helpers receive a dead EAX besides their CSkinMesh in ECX, so they are cdecl functions
 * with the registers first; the wrappers are plain thiscall methods. */
#include "game/skinmesh.h"

ORIG_DATA(00611290); /* CSkinMesh::vftable */
ORIG_DATA(00611294); /* ".\\SkinMesh.cpp" */
ORIG_DATA(006112A4); /* the missing-file message, cp1251 */
ORIG_DATA(0069916C); /* _ThrowInfo of CGameException */

ORIG_THISCALL(004AC890, void, (void *self));              /* CRenderObject::SetWorldTransform */
ORIG_FN(004AC690, void, (void *self, void *unusedEax));   /* CRenderObject3D::Tick */

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

/* The sub-object draws: the skeleton sub object's slots take the clip group, the frame, the table values (slot
 * 1 takes both the second value - or the wrapper's fallback when it is zero - and the first; slot 3 only the
 * first).  The matrix sub object's table has the same shape. */
typedef void (__thiscall *SubObjectDraw4)(SkinSubObject *self, void *clips, unsigned int frame, void *second,
                                          void *first);
typedef void (__thiscall *SubObjectDraw3)(SkinSubObject *self, void *clips, unsigned int frame, void *first);

/* 0x4C0620: every sub object, with the draw-table entry after its own (the table is one entry longer than the
 * mesh list) and the fallback for a zero second value. */
DECOMP(004C0620)
void __cdecl DrawSkinSubObjectsEx(CSkinMesh *self, void *unusedEax, void *clips, unsigned int frame,
                                  const MeshDrawTable *table, void *fallback)
{
    (void)unusedEax;
    for (unsigned int i = 0;
         self->objects.begin != nullptr && i < (unsigned int)(self->objects.end - self->objects.begin); i++) {
        SkinSubObject *object = self->objects.begin[i];
        void *second = table->begin[i + 1].second ? table->begin[i + 1].second : fallback;
        void *first = table->begin[i + 1].first;
        ((SubObjectDraw4)((void **)object->vftable)[1])(object, clips, frame, second, first);
    }
}

/* 0x4C0680: the same walk, calling the third slot with the first table value only. */
DECOMP(004C0680)
void __cdecl DrawSkinSubObjects(CSkinMesh *self, void *unusedEax, void *clips, unsigned int frame,
                                const MeshDrawTable *table)
{
    (void)unusedEax;
    for (unsigned int i = 0;
         self->objects.begin != nullptr && i < (unsigned int)(self->objects.end - self->objects.begin); i++) {
        SkinSubObject *object = self->objects.begin[i];
        void *first = table->begin[i + 1].first;
        ((SubObjectDraw3)((void **)object->vftable)[3])(object, clips, frame, first);
    }
}

/* --- SkinMeshObject ------------------------------------------------------------------------------------- */

/* the animation group at +0x1EC: the clips it holds (the first one supplies the frame count) */
struct AnimationClipGroup {
    unsigned char unknown0[4]; /* +00 */
    void **begin;              /* +04 */
    void **end;                /* +08 */
    void **limit;              /* +0C */
};

struct AnimationClip {
    unsigned char unknown0[8]; /* +00 */
    int frameCount;            /* +08 */
};

/* the source/destination bone table of 0x4C0BF0, 36 words (the original writes it as interleaved word and dword
 * stores; this is the resulting memory) */
static const unsigned short kSkinPalette[36] = {
    0, 2, 1, 1, 2, 3, 0, 4, 6, 0, 6, 2,
    0, 5, 4, 0, 1, 5, 7, 5, 1, 3, 7, 1,
    2, 6, 3, 3, 6, 7, 4, 5, 7, 4, 7, 6,
};

/* 0x4C0B20: the base update, then the frame advances one step and wraps at the clip's last frame (a comparison
 * for equality, as the original has it). */
DECOMP(004C0B20)
void __cdecl TickSkinMeshObject(SkinMeshObject *self, void *unusedEax)
{
    sub_004AC690(self, unusedEax);
    if (self->animated) {
        self->frame++;
        if (self->frame == (unsigned int)self->frameCount)
            self->frame = 0;
    }
}

/* 0x4C0BF0: the animation state is reset for the first animation frame.  The frame count comes from the first
 * clip of the group (an empty group is not expected: the original reads the count through a null pointer);
 * the mesh count from the mesh vector.  The palette is the original's constant source/destination bone table,
 * which is 36 words (as stored by the interleaved word and dword writes of the function). */
DECOMP(004C0BF0)
void SkinMeshObject::ResetAnimation()
{
    AnimationClipGroup *group = (AnimationClipGroup *)animation;
    void **clipBegin = group->begin;
    AnimationClip *clip = nullptr;
    if (clipBegin != nullptr && clipBegin != group->end)
        clip = (AnimationClip *)clipBegin[0];
    frameCount = clip->frameCount;

    meshCount = meshes.begin != nullptr ? (unsigned int)(meshes.end - meshes.begin) : 0;
    __builtin_memcpy(palette, kSkinPalette, sizeof palette);
    currentMesh = 0;
    frame = 0;
    animated = 1;
}

/* 0x4C0DE0: draw mesh `index` (clamped to the last one) with the world transform set first. */
DECOMP(004C0DE0)
void SkinMeshObject::Draw(unsigned int index)
{
    if (index >= meshCount)
        index = meshCount - 1;
    sub_004AC890(this);
    DrawSkinSubObjectsEx(meshes.begin[index], nullptr, animation, frame, &drawTable, fallback);
}

/* 0x4C0E30: draw the current mesh without the world transform. */
DECOMP(004C0E30)
void SkinMeshObject::DrawCurrent()
{
    DrawSkinSubObjects(meshes.begin[currentMesh], nullptr, animation, frame, &drawTable);
}

/* 0x4C0E60: draw mesh `index` (clamped) without the world transform. */
DECOMP(004C0E60)
void SkinMeshObject::Draw3(unsigned int index)
{
    if (index >= meshCount)
        index = meshCount - 1;
    DrawSkinSubObjects(meshes.begin[index], nullptr, animation, frame, &drawTable);
}

/* 0x4C0EA0: the four-argument draw without setting the world transform. */
DECOMP(004C0EA0)
void SkinMeshObject::DrawNoWorld(unsigned int index)
{
    if (index >= meshCount)
        index = meshCount - 1;
    DrawSkinSubObjectsEx(meshes.begin[index], nullptr, animation, frame, &drawTable, fallback);
}
