/* 0x0043AE60: CClock vf2_3C: builds a script table from the clock's entries [0x30..0x34), asking each one
 * through slot 8 to add its fields to the table, then stores the table under "Time" (0x609E8C) in the
 * argument object and destroys the temporary. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_43AE60;
DECOMP_C void __thiscall sub_00435E00(void *self, int allocator);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_0057BF50(void *self, char *name, void *table);
DECOMP_C char d_00609E8C[];
typedef void (__thiscall *vf_43AE60)(void *self, void *table);

DECOMP(0043AE60)
void __thiscall f_0043AE60(char *this, void *arg)
{
    Tbl_43AE60 table;
    char **p;

    sub_00435E00(&table, 0);
    for (p = *(char ***)(this + 0x30); p != *(char ***)(this + 0x34); p++) {
        void *entry = *p;
        ((vf_43AE60)(*(void ***)entry)[8 / 4])(entry, &table);
    }
    sub_0057BF50(arg, d_00609E8C, &table);
    sub_004220A0(&table);
}
