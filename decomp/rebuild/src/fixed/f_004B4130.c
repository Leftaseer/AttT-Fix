/* 0x004B4130: Serializable::~Serializable: takes the Serializable vftable (0x610D00), unregisters the object from the
 * global serializator (0x6CA34C, through 0x004B5700) and destroys the _Object base (0x00422000). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B5700(void *self, void *item);
DECOMP_C void __thiscall sub_00422000(void *self);
DECOMP_C char d_00610D00[], d_006CA34C[];

DECOMP(004B4130)
void __thiscall f_004B4130(void *this)
{
    *(char **)this = d_00610D00;
    sub_004B5700(*(void **)d_006CA34C, this);
    sub_00422000(this);
}
