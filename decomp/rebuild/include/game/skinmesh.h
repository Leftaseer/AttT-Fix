/* CSkinMesh: one skinned mesh read from its own file (0x74 bytes).  Load (0x4C07C0) opens the name through a
 * CGameFile, reads a count of skeleton sub objects (each built by 0x4BD0F0 on 0x100 bytes) and a count of matrix
 * sub objects (0x475720 on 0x7C bytes) into the one vector at +04, then a 0x60-byte block the file supplies
 * verbatim.  The destructor deletes every sub object through its own virtual table (slot 0, flag 1).
 *
 * The constructor (0x4C0A10) takes the name by value - an MSVC 2005 std::string of seven words, the same shape
 * the loaders pass their file names in - and the callee destroys that argument, so it is declared as raw storage
 * here (the build's convention check counts its words). */
#pragma once
#include "game/common.h"
#include "game/gamefile.h"

typedef struct { unsigned int w[7]; } Str_4C07C0; /* std::string passed by value */

/* a sub object the vector holds (skeleton 0x100 bytes, matrix 0x7C bytes); only the deleting destructor of
 * vtable slot 0 is used here */
struct SkinSubObject {
    void *vftable; /* +00 */
};

/* the engine's vector storage (0x10 bytes): the fixed allocator slot, then the three pointers */
struct SkinSubObjectVector {
    unsigned char allocator[4]; /* +00 */
    SkinSubObject **begin;      /* +04 */
    SkinSubObject **end;        /* +08 */
    SkinSubObject **limit;      /* +0C */
};
static_assert(sizeof(SkinSubObjectVector) == 0x10, "SkinSubObjectVector is 0x10 bytes");
static_assert(__builtin_offsetof(SkinSubObjectVector, begin) == 0x04, "SkinSubObjectVector::begin");

struct CSkinMesh {
    void *vftable;                /* +00 0x611290 */
    SkinSubObjectVector objects;  /* +04 */
    unsigned char unknown14[0x60]; /* +14 read straight from the file */

    CSkinMesh(Str_4C07C0 name); /* 0x4C0A10 */
    ~CSkinMesh();               /* 0x4C06D0 */
    void Load(Str_4C07C0 name); /* 0x4C07C0 */
};
static_assert(sizeof(CSkinMesh) == 0x74, "CSkinMesh is 0x74 bytes");
static_assert(__builtin_offsetof(CSkinMesh, objects) == 0x04, "CSkinMesh::objects");
static_assert(__builtin_offsetof(CSkinMesh, unknown14) == 0x14, "CSkinMesh::unknown14");

/* the deleting destructor 0x4C07A0, the vector shape's vtable slot 0 */
CSkinMesh *__thiscall DeleteSkinMesh(CSkinMesh *self, unsigned char flags);

/* ---------------------------------------------------------------------------------------------------------
 * SkinMeshObject: the render object that owns a list of meshes and plays one animation over them (vftable
 * 0x6112C4; its render interface table 0x611384 holds the four draw methods below).  The constructor 0x4C0FE0
 * is not translated yet. */

/* the per-mesh draw table at +0x238: a vector of 8-byte entries, one per mesh plus a leading one (sub object i
 * draws with the entry after its own) */
struct MeshDrawEntry {
    void *first;  /* +00 */
    void *second; /* +04 */
};

struct MeshDrawTable {
    unsigned char allocator[4]; /* +00 */
    MeshDrawEntry *begin;       /* +04 */
    MeshDrawEntry *end;         /* +08 */
    MeshDrawEntry *limit;       /* +0C */
};
static_assert(sizeof(MeshDrawTable) == 0x10, "MeshDrawTable is 0x10 bytes");
static_assert(__builtin_offsetof(MeshDrawTable, begin) == 0x04, "MeshDrawTable::begin");

struct SkinMeshVector {
    unsigned char allocator[4]; /* +00 */
    CSkinMesh **begin;          /* +04 */
    CSkinMesh **end;            /* +08 */
    CSkinMesh **limit;          /* +0C */
};
static_assert(sizeof(SkinMeshVector) == 0x10, "SkinMeshVector is 0x10 bytes");
static_assert(__builtin_offsetof(SkinMeshVector, begin) == 0x04, "SkinMeshVector::begin");

struct SkinMeshObject {
    void *vftable;                  /* +000 0x6112C4 */
    unsigned char unknown04[0x38];  /* +004 */
    void *fallback;                 /* +03C the fourth argument of the four-argument sub-object draws */
    unsigned char unknown40[0x188]; /* +040 */
    int frameCount;                 /* +1C8 frames of the current clip */
    unsigned int meshCount;         /* +1CC */
    unsigned int currentMesh;       /* +1D0 */
    unsigned char animated;         /* +1D4 */
    unsigned char unknown1D5[3];    /* +1D5 */
    unsigned int frame;             /* +1D8 */
    SkinMeshVector meshes;          /* +1DC */
    void *animation;                /* +1EC the clip group (a vector of clips at +04) */
    unsigned short palette[36];     /* +1F0 the bone table 0x4C0BF0 fills */
    MeshDrawTable drawTable;        /* +238 */

    void Tick();                     /* 0x4C0B20, cdecl shim: TickSkinMeshObject */
    void ResetAnimation();           /* 0x4C0BF0 */
    void Draw(unsigned int index);   /* 0x4C0DE0 */
    void DrawCurrent();              /* 0x4C0E30 */
    void Draw3(unsigned int index);  /* 0x4C0E60 */
    void DrawNoWorld(unsigned int index); /* 0x4C0EA0 */
};
static_assert(__builtin_offsetof(SkinMeshObject, fallback) == 0x03C, "SkinMeshObject::fallback");
static_assert(__builtin_offsetof(SkinMeshObject, frameCount) == 0x1C8, "SkinMeshObject::frameCount");
static_assert(__builtin_offsetof(SkinMeshObject, meshCount) == 0x1CC, "SkinMeshObject::meshCount");
static_assert(__builtin_offsetof(SkinMeshObject, currentMesh) == 0x1D0, "SkinMeshObject::currentMesh");
static_assert(__builtin_offsetof(SkinMeshObject, animated) == 0x1D4, "SkinMeshObject::animated");
static_assert(__builtin_offsetof(SkinMeshObject, frame) == 0x1D8, "SkinMeshObject::frame");
static_assert(__builtin_offsetof(SkinMeshObject, meshes) == 0x1DC, "SkinMeshObject::meshes");
static_assert(__builtin_offsetof(SkinMeshObject, animation) == 0x1EC, "SkinMeshObject::animation");
static_assert(__builtin_offsetof(SkinMeshObject, palette) == 0x1F0, "SkinMeshObject::palette");
static_assert(__builtin_offsetof(SkinMeshObject, drawTable) == 0x238, "SkinMeshObject::drawTable");

/* 0x4C0B20 receives the this pointer in ECX and an unused EAX, so it is a cdecl function with the registers
 * first (the adapter of the build moves them) */
void __cdecl TickSkinMeshObject(SkinMeshObject *self, void *unusedEax);
