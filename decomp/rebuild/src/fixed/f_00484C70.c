/* 0x00484C70: NPCCollector::NPCCollector (the 0x38-byte singleton that 0x004B0AA0 allocates): takes the NPCCollector
 * vftable (0x60F628), builds the member at +4 (0x00484AA0, both of its arguments the same indeterminate byte), makes
 * the script table at +0x2C (0x607CC4 vftable, 0, -1) and fills it from the "WorldNPC" table: a table from pool 0
 * (0x00435E00) is assigned to it (0x0057A860), a table from pool -10002 (0x0045C7E0) is queried (0x0057BF50, name
 * 0x60F62C) into it; each temporary is destroyed (0x004220A0). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00484AA0(void *self, const void *flag, const void *flag_copy);
DECOMP_C void __thiscall sub_00435E00(void *self, int pool);
DECOMP_C void __thiscall sub_0057A860(void *self, const void *table);
DECOMP_C void __thiscall sub_0045C7E0(void *self, int pool);
DECOMP_C void __thiscall sub_0057BF50(void *self, const void *name, void *table);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C char d_0060F628[], d_00607CC4[], d_0060F62C[];

DECOMP(00484C70)
char *__thiscall f_00484C70(char *this)
{
    char table[0xc];
    char flag;
    *(char **)this = d_0060F628;
    sub_00484AA0(this + 4, &flag, &flag);
    *(char **)(this + 0x2c) = d_00607CC4;
    *(unsigned int *)(this + 0x30) = 0;
    *(unsigned int *)(this + 0x34) = (unsigned int)-1;
    sub_00435E00(table, 0);
    sub_0057A860(this + 0x2c, table);
    sub_004220A0(table);
    sub_0045C7E0(table, -10002);
    sub_0057BF50(table, d_0060F62C, this + 0x2c);
    sub_004220A0(table);
    return this;
}
