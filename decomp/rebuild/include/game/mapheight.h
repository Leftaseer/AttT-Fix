/* CMapHeight: the terrain height field of the current world (0x30 bytes, a CSingleton<CMapHeight> whose instance
 * is 0x6C88E4).  Load (0x473370) reads "<path>.nmph": width (x cells), depth (z cells), origin x/z as ints, then
 * one row of depth unsigned shorts per x, then the scale and the offset.  Height (0x473110) interpolates
 * bilinearly inside a cell and returns -9999 outside the grid.  The instance is built on first request
 * (0x433620). */
#pragma once
#include "game/common.h"

struct CMapHeight {
    void *vftable;          /* +00 */
    unsigned short **rows;  /* +04 width rows of depth samples */
    int width;              /* +08 cells along x */
    int depth;              /* +0C cells along z */
    int originX;            /* +10 world x of cell 0 */
    int originZ;            /* +14 world z of cell 0 */
    float minX;             /* +18 */
    float maxX;             /* +1C */
    float minZ;             /* +20 */
    float maxZ;             /* +24 */
    float scale;            /* +28 */
    float offset;           /* +2C */

    CMapHeight();                              /* 0x473360 */
    ~CMapHeight();                             /* 0x473540 */
    CMapHeight *Destroy(int flags);            /* 0x473590 scalar deleting destructor */
    void Load(const std::string &path, void *unused); /* 0x473370 */
    float Height(float x, float z);            /* 0x473110 */
    static CMapHeight *Instance();             /* 0x433620 */
};
static_assert(sizeof(CMapHeight) == 0x30, "CMapHeight is 0x30 bytes");
static_assert(__builtin_offsetof(CMapHeight, rows) == 0x04, "CMapHeight::rows");
static_assert(__builtin_offsetof(CMapHeight, width) == 0x08, "CMapHeight::width");
static_assert(__builtin_offsetof(CMapHeight, maxX) == 0x1C, "CMapHeight::maxX");
static_assert(__builtin_offsetof(CMapHeight, scale) == 0x28, "CMapHeight::scale");
