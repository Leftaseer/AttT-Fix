/* 0x004270B0: loads the +0x44 slot from the file-name argument (0x00458B50); the result is ignored. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_00458B50(void *self, const void *name);

DECOMP(004270B0)
void __thiscall f_004270B0(void *this, void *name)
{
    sub_00458B50((char *)this + 0x44, name);
}
