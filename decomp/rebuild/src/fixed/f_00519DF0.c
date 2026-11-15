/* Lua_006C6A20::GetDeadTroops 0x00519DF0: the wrapper's level object (+0xBC) troop list (+0x50 array,
 * +0x54 count, 0xC8-byte elements) as the table of {liter, name, qn} tables, one per element whose
 * bit vector (+0x88/+0x8C) is non-empty.  The rawgeti pushes the outer table, then the temporaries die. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_519DF0;                  /* nScript::Table */
typedef struct { void *vftable; void *child; int built; } Obj_519DF0;
DECOMP_C void *__thiscall sub_00435E00(void *self, int allocator); /* nScript::Table::Table */
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void __thiscall sub_0057BDF0(void *t, const char *key, const char *v);
DECOMP_C void __thiscall sub_0057BEA0(void *t, int idx, void *inner);
DECOMP_C int __thiscall sub_0051DC20(void *self);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);       /* lua_rawgeti */
DECOMP_C void __thiscall sub_00422000(void *self);                 /* nScript::Object::~Object */
DECOMP_C void __thiscall sub_004220A0(void *self);                 /* nScript::Table::~Table */
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C char d_008D122C[], d_0060826C[], d_00607CB8[], d_006136D4[], d_00689F04[], d_0060FF30[];

DECOMP(00519DF0)
int __thiscall f_00519DF0(void *self, void *lua)
{
    char *this = (char *)self;
    char *level = *(char **)(this + 0xbc);
    char *array = *(char **)(level + 0x50);
    int count = *(int *)(level + 0x54);
    Tbl_519DF0 outer;
    Obj_519DF0 object;
    int i, index;
    (void)lua;
    sub_00435E00(&outer, 0);
    for (i = 0, index = 1; i < count; i++) {
        char *element = array + i * 0xc8;
        char *owner = *(char **)(element + 0x58);
        Tbl_519DF0 inner;
        if (sub_0051DC20(element) == 0)
            continue;
        sub_00435E00(&inner, 0);
        sub_0057BC80(&inner, d_006136D4, (float)i);                              /* "liter" */
        sub_0057BDF0(&inner, d_00689F04, imp_0060732C(*(char **)owner + 8));     /* "name" */
        sub_0057BC80(&inner, d_0060FF30, (float)sub_0051DC20(element));          /* "qn" */
        sub_0057BEA0(&outer, index++, &inner);
        sub_004220A0(&inner);
    }
    object.vftable = d_0060826C;
    object.child = 0;
    object.built = 0;
    sub_00403390(*(void **)d_008D122C, -10000, (int)outer.w[2]);
    object.built = 1;
    object.vftable = d_00607CB8;
    sub_00422000(&object);
    sub_004220A0(&outer);
    return 1;
}
