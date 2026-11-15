/* 0x004278E0: releases an nScript handle object: the base vtable 0x00607CB8, then the _Object destructor
 * (0x00422000, which throws when +4 is still set). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607CB8[];
DECOMP_C unsigned int __thiscall sub_00422000(void *self);             /* _Object::~_Object */

DECOMP(004278E0)
void __thiscall f_004278E0(void *this)
{
    *(void **)this = d_00607CB8;
    sub_00422000(this);
}
