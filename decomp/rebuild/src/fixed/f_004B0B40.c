/* 0x004B0B40: constructs the clock-table base from a named script handle, installs the interface vtables and returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00437970(void *self, void *handle, int flag);
DECOMP_C void __thiscall sub_00532120(void *self, void *handle);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C char d_006107E0[], d_00610704[], d_006106F4[], d_006106D4[], d_006106C0[], d_006106B8[], d_006106AC[];

DECOMP(004B0B40)
void *__thiscall f_004B0B40(void *self)
{
    char *this = self;
    unsigned int handle[6];
    sub_00532120(this, sub_00437970(handle, d_006107E0, 1));
    sub_00427820(handle);
    *(char **)this = d_00610704;
    *(char **)(this + 0x1f4) = d_006106F4;
    *(char **)(this + 0x1fc) = d_006106D4;
    *(char **)(this + 0x250) = d_006106C0;
    *(char **)(this + 0x258) = d_006106B8;
    *(char **)(this + 0x25c) = d_006106AC;
    *(unsigned int *)(this + 0x374) = 0;
    return this;
}
