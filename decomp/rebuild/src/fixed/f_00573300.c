/* 0x00573300: constructs an object from a by-value nScript::Table and one scalar: the base
 * consumes a copy, the vtable and +0x74 are initialized, +0x78 becomes a 16-slot zero-filled
 * array, and the incoming table is destroyed.  Returns this. */
/* @conv ECX 16 */
#include "auto_pre.h"

typedef struct {
    unsigned int words[3];
} Table_00573300;

DECOMP_C void __thiscall sub_00435D90(void *self, const void *src);
DECOMP_C void __thiscall sub_00571940(void *self, Table_00573300 table, unsigned int value);
DECOMP_C void __thiscall sub_00591D70(void *self, unsigned int count, void *value);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C char d_0061D2CC[];

DECOMP(00573300)
void *__thiscall f_00573300(char *this, Table_00573300 table, unsigned int value)
{
    Table_00573300 copy;
    void *zero = 0;

    sub_00435D90(&copy, &table);
    sub_00571940(this, copy, value);
    *(void **)this = d_0061D2CC;
    *(unsigned int *)(this + 0x74) = 0;
    sub_00591D70(this + 0x78, 0x10, &zero);
    sub_004220A0(&table);
    return this;
}
