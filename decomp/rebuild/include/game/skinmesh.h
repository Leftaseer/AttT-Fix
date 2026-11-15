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
#include "game/filesystem.h"
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
 * 0x6112C4; its render interface table 0x611384 holds the four draw methods below). */

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

/* std::vector<std::string>: the elements are the 28-byte MSVC strings */
struct StringVector {
    unsigned char allocator[4]; /* +00 */
    std::string *begin;         /* +04 */
    std::string *end;           /* +08 */
    std::string *limit;         /* +0C */
};
static_assert(sizeof(StringVector) == 0x10, "StringVector is 0x10 bytes");
static_assert(__builtin_offsetof(StringVector, begin) == 0x04, "StringVector::begin");

/* ---------------------------------------------------------------------------------------------------------
 * The animation manager (0x4C0EE0 creates it once, 0x4C01B0 fills it): a vtable and two of the file system's
 * string maps - the loaded models by their lowered name, the animation clips by name. */

/* the model record the cache keeps and the object copies its vectors from */
struct SkinModelRecord {
    SkinMeshVector meshes;   /* +00 */
    MeshDrawTable drawTable; /* +10 */
};
static_assert(sizeof(SkinModelRecord) == 0x20, "SkinModelRecord is 0x20 bytes");

/* a node of the model cache: the string key, then the record */
struct SkinModelNode {
    FsStringNode head;      /* +00 next, prev and the name at +08 */
    SkinModelRecord record; /* +24 */
};
static_assert(__builtin_offsetof(SkinModelNode, record) == 0x24, "SkinModelNode::record");

/* a node of the clip map: the string key, then the clip 0x4BD930 builds (0x38 bytes) */
struct SkinAnimationNode {
    FsStringNode head; /* +00 */
    void *animation;   /* +24 */
};
static_assert(__builtin_offsetof(SkinAnimationNode, animation) == 0x24, "SkinAnimationNode::animation");

struct CSkinAnimationManager {
    void *vftable;        /* +00 0x611254 */
    FsHashMap models;     /* +04 map<string, SkinModelNode> */
    FsHashMap animations; /* +2C map<string, SkinAnimationNode> */
};
static_assert(sizeof(CSkinAnimationManager) == 0x54, "CSkinAnimationManager is 0x54 bytes");
static_assert(__builtin_offsetof(CSkinAnimationManager, models) == 0x04, "CSkinAnimationManager::models");
static_assert(__builtin_offsetof(CSkinAnimationManager, animations) == 0x2C, "CSkinAnimationManager::animations");

/* 0x4C01B0 fills the vtable and the two empty maps; 0x4C0EE0 builds it once and keeps it in the global
 * 0x6CA490 (the objects count themselves in 0x6CA48C). */
CSkinAnimationManager *__thiscall InitSkinAnimationManager(CSkinAnimationManager *self); /* 0x4C01B0 */
void *__cdecl GetSkinAnimationManager();                                                 /* 0x4C0EE0 */

/* the effect object 0x448F10 hands out (0x6CAA28 holds one): 0x447A50 builds it with its file name at +04 */
struct Effect {
    void *vftable;        /* +00 */
    std::string fileName; /* +04 */
};
static_assert(__builtin_offsetof(Effect, fileName) == 0x04, "Effect::fileName");

struct SkinMeshObject {
    void *vftable;                  /* +000 0x6112C4 */
    unsigned char unknown04[4];     /* +004 */
    std::string name;               /* +008 the model name, copied by the constructors */
    unsigned char unknown24[0x18];  /* +024 */
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

/* Splits the text at every separator (a model name is "model;frames;animation"); the tail after the last
 * separator is always a part, empty or not. */
StringVector *__cdecl SplitStringVector(StringVector *parts, const std::string *text, char separator); /* 0x4F7290 */
/* std::vector<std::string>'s destructor; the original receives a dead EAX besides the vector in ECX */
void __cdecl DestroyStringVector(StringVector *parts, unsigned int unusedEax); /* 0x434A60 */

/* 0x4C0240: fills the object's meshes and draw table with the model of the name (from the manager's cache,
 * reloading the castle gate bar) and looks the animation clip up by the third token. */
void __thiscall LoadSkinModel(CSkinAnimationManager *self, const std::string *name, SkinMeshVector *meshes,
                              void **animation, MeshDrawTable *drawTable);

/* The lifetime, spelled out as thiscall helpers returning the object in EAX as the original's callers expect.
 * Both constructors copy the name, attach the object to the animation manager and reset the animation; the second
 * takes the effect of an already loaded model instead of an effect name.  0x4C12B0 is the deleting destructor. */
SkinMeshObject *__thiscall InitSkinMeshObject(SkinMeshObject *self, const std::string &name,
                                              const std::string &effectName); /* 0x4C0FE0 */
SkinMeshObject *__thiscall InitSkinMeshObjectFromEffect(SkinMeshObject *self, const std::string &name,
                                                        const Effect *effect); /* 0x4C1100 */
void __thiscall DestroySkinMeshObject(SkinMeshObject *self);               /* 0x4C11D0 */
SkinMeshObject *__thiscall DeleteSkinMeshObject(SkinMeshObject *self, unsigned char flags); /* 0x4C12B0 */
