/* CMapHeight: the terrain height field and its singleton lifetime (see game/mapheight.h). */
#include "game/common.h"
#include "game/globals.h"
#include "game/mapheight.h"
#include "game/gamefile.h"

ORIG_DATA(0060E75C);  /* CSingleton<CMapHeight>::vftable */
ORIG_DATA(0060E764);  /* CMapHeight::vftable */
ORIG_DATA(0060B7A0);  /* double: 5.0 world units between the cells */
ORIG_DATA(00607BC8);  /* "Ошибка при создании m_instance в CSingleton" */
ORIG_DATA(00607BAC);  /* "e:\\prog\\att1\\Singleton.h" */

ORIG_FN(005E3B10, void *, (unsigned int size)); /* operator new[] */

inline void *operator new(unsigned int, void *p) { return p; }

/* The singleton accessor: the object is built on the first request, and a failed allocation throws the CSingleton
 * error instead of returning null. */
DECOMP(00433620)
CMapHeight *CMapHeight::Instance()
{
    if (!g_mapHeight) {
        void *memory = operator new(sizeof(CMapHeight));
        g_mapHeight = memory ? new (memory) CMapHeight() : nullptr;
        if (!g_mapHeight)
            ThrowGameException(ORIG_STR(00607BC8), ORIG_STR(00607BAC), 16);
    }
    return g_mapHeight;
}

DECOMP(00473360)
CMapHeight::CMapHeight()
{
    vftable = d_0060E764;
    rows = nullptr;
}

/* the rows are released bottom-up through delete[] and the object then drops to the CSingleton vtable */
DECOMP(00473540)
CMapHeight::~CMapHeight()
{
    vftable = d_0060E764;
    if (rows) {
        for (int i = 0; i < width; i++)
            operator delete[](rows[i]);
        operator delete[](rows);
    }
    vftable = d_0060E75C;
}

DECOMP(00473590)
CMapHeight *CMapHeight::Destroy(int flags)
{
    this->~CMapHeight();
    if (flags & 1)
        operator delete(this);
    return this;
}

/* Reads the terrain from "<path>.nmph": the two grid dimensions and the world position of cell 0, one row of
 * samples per x, then the scale and offset.  The rows are allocated with the dimensions exactly as the file has
 * them; the bounds are the corners of the cell grid (cell size 5.0).  The second argument is unused. */
DECOMP(00473370)
void CMapHeight::Load(const std::string &path, void *unused)
{
    (void)unused;
    const double cellSize = ORIG_VAR(0060B7A0, double);

    std::string fileName = path + ".nmph";
    CGameFile file;
    file.Open(fileName, 1);
    if (!file.opened)
        return;

    file.Read(&width, 4);
    file.Read(&depth, 4);
    file.Read(&originX, 4);
    file.Read(&originZ, 4);

    minX = (float)originX;
    maxX = minX + (double)(width - 1) * cellSize;
    minZ = (float)originZ;
    maxZ = (double)(depth - 1) * cellSize + minZ;

    rows = (unsigned short **)sub_005E3B10((unsigned int)(width * 4));
    for (int i = 0; i < width; i++)
        rows[i] = (unsigned short *)sub_005E3B10((unsigned int)(depth * 2));
    for (int i = 0; i < width; i++)
        file.Read(rows[i], depth * 2);

    file.Read(&scale, 4);
    file.Read(&offset, 4);
    file.Close();
}
