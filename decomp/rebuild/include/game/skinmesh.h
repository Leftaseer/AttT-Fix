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
