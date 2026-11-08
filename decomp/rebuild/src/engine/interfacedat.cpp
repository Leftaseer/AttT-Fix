/* CReadInterfaceDat: the interface record table and its lifetime (0x4A7160 / 0x4A70C0). */
#include "game/common.h"
#include "game/interfacedat.h"

ORIG_DATA(00610088); /* CReadInterfaceDat::vftable */
ORIG_DATA(00610080); /* CSingleton<CReadInterfaceDat>::vftable */

ORIG_THISCALL(004A7040, void *, (void *map, const void *alloc, const void *comp)); /* ctor of map<string, entry> */
ORIG_FASTCALL(00422AD0, void, (void *self));                           /* clear the record map */

/* the original hands the map ctor an uninitialised stack byte for the empty allocator; nothing reads it */
DECOMP(004A7160)
CReadInterfaceDat::CReadInterfaceDat()
{
    char allocator = 0;
    vftable = d_00610088;
    sub_004A7040(&map, &allocator, &allocator);
}

DECOMP(004A70C0)
CReadInterfaceDat::~CReadInterfaceDat()
{
    vftable = d_00610088;

    if (map.begin)
        operator delete(map.begin);
    map.begin = nullptr;
    map.end = nullptr;
    map.limit = nullptr;

    /* the tree part at map+4 destroys the keys and the records and frees the nodes */
    sub_00422AD0((char *)&map + 4);
    operator delete(map.sentinel);
    map.sentinel = nullptr;

    vftable = d_00610080;
}
