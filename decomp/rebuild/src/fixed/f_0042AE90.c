/* 0x0042AE90: CCritKeyAnimation's constructor: the CSimpleAnimation base and vtable 0x00608534. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C char d_00608534[];
DECOMP_C void *__thiscall sub_0042A530(void *self, void *name, void *driven, unsigned int owning);

DECOMP(0042AE90)
void *__thiscall f_0042AE90(char *this, char *name, char *driven, unsigned int owning)
{
    sub_0042A530(this, name, driven, owning);
    *(void **)this = d_00608534;
    return this;
}
