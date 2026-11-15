/* Lua_006C6A20::GetPos 0x00513540: the wrapper's position (+0x64 x, +0x68 y, +0x6C z) as the table {x, y, z}.
 * A fresh nScript::Table (0x435E00) gets the three floats, the rawgeti pushes it and the temporary
 * nScript::Object is destroyed, then the table (whose ref the rawgeti read). */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_513540;                 /* nScript::Table */
DECOMP_C void *__thiscall sub_00435E00(void *self, int allocator); /* nScript::Table::Table */
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);      /* lua_rawgeti */
DECOMP_C void __thiscall sub_00422000(void *self);                /* nScript::Object::~Object */
DECOMP_C void __thiscall sub_004220A0(void *self);                /* nScript::Table::~Table */
DECOMP_C char d_008D122C[], d_0060826C[], d_00607CB8[], d_006098D0[], d_006098CC[], d_006098C8[];

typedef struct { void *vftable; void *child; int built; } Obj_513540;

DECOMP(00513540)
int __thiscall f_00513540(void *self, void *lua)
{
    char *this = (char *)self;
    Tbl_513540 table;
    Obj_513540 object;
    (void)lua;
    sub_00435E00(&table, 0);
    sub_0057BC80(&table, d_006098D0, *(float *)(this + 0x64)); /* "x" */
    sub_0057BC80(&table, d_006098CC, *(float *)(this + 0x68)); /* "y" */
    sub_0057BC80(&table, d_006098C8, *(float *)(this + 0x6c)); /* "z" */
    object.vftable = d_0060826C;
    object.child = 0;
    object.built = 0;
    sub_00403390(*(void **)d_008D122C, -10000, (int)table.w[2]);
    object.built = 1;
    object.vftable = d_00607CB8;
    sub_00422000(&object);
    sub_004220A0(&table);
    return 1;
}
