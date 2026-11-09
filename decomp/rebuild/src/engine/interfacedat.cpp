/* CReadInterfaceDat: the interface record table and its lifetime (0x4A7160 / 0x4A70C0) and its loader (0x4A71E0). */
#include "game/common.h"
#include "game/interfacedat.h"
#include "game/gamefile.h"

ORIG_DATA(00610088); /* CReadInterfaceDat::vftable */
ORIG_DATA(00610080); /* CSingleton<CReadInterfaceDat>::vftable */
ORIG_DATA(006CA280); /* the CGameFile reader the dat loaders share */
ORIG_DATA(006CA278); /* bytes of the open file the lexer has not read yet */
ORIG_DATA(006CA2BC); /* the token the lexer returned last */

ORIG_THISCALL(004A7040, void *, (void *map, const void *alloc, const void *comp)); /* ctor of map<string, entry> */
ORIG_FASTCALL(00422AD0, void, (void *self));                           /* clear the record map */
ORIG_THISCALL(004EF350, void, (void *vector, unsigned count, void *sentinel)); /* refill the bucket vector */
ORIG_FN(00470410, int, ());                                            /* the next token of the file */
ORIG_THISCALL(004A6610, void *, (void *record));                       /* record ctor */
ORIG_THISCALL(004A6D30, void, (void *record));                         /* read the record's fields */
ORIG_THISCALL(00424270, void *, (void *map, const void *key));         /* find the record's node, or insert one */
ORIG_THISCALL(004A6E90, void *, (void *value, const void *record));    /* value = record */
ORIG_THISCALL(004A6740, void, (void *record));                         /* record dtor */

/* one record of the interface dat (0x138 bytes); its first member is the name string the map keys it by, and the
 * record ctor/parser/dtor (0x4A6610 / 0x4A6D30 / 0x4A6740) own all its fields. */
struct InterfaceRecord {
    alignas(4) unsigned char bytes[0x138];
};
static_assert(sizeof(InterfaceRecord) == 0x138, "InterfaceRecord is 0x138 bytes");

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

/* The loaders share one CGameFile (it reads the whole file into memory), then the lexer (0x470410) walks it token
 * by token: a token 0x141 starts a record whose fields follow up to token 0x103, and the map is keyed by the
 * record's name (its first string). */
DECOMP(004A71E0)
void CReadInterfaceDat::Load(const std::string &name)
{
    CGameFile *reader = (CGameFile *)d_006CA280;
    reader->Open(name, 1);
    ORIG_VAR(006CA278, unsigned) = reader->file->size;

    sub_00422AD0((char *)&map + 4);
    void *sentinel = map.sentinel;
    sub_004EF350(&map.vectorAlloc, 9, &sentinel);
    map.mask = 1;
    map.count = 1;

    ORIG_VAR(006CA2BC, int) = sub_00470410();
    while (ORIG_VAR(006CA2BC, int) != 0) {
        if (ORIG_VAR(006CA2BC, int) == 0x141) {
            InterfaceRecord record;
            sub_004A6610(&record);
            sub_004A6D30(&record);
            void *value = sub_00424270(&map, &record);
            sub_004A6E90(value, &record);
            sub_004A6740(&record);
        }
        ORIG_VAR(006CA2BC, int) = sub_00470410();
    }
    reader->Close();
}
