/* 0x004B40E0: constructor of the object whose vtable is 0x610D00: clears +4 and registers itself with the
 * manager reached through the singleton pointer at 0x6CA34C. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00610D00[], d_006CA34C[];
DECOMP_C void __thiscall sub_004B5880(void *self, void *node);

DECOMP(004B40E0)
void *__thiscall f_004B40E0(char *this)
{
    *(char **)this = d_00610D00;
    *(unsigned int *)(this + 4) = 0;
    sub_004B5880(*(void **)d_006CA34C, this);
    return this;
}
