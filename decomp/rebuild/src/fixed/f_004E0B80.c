/* 0x004E0B80: CTextureNode::Render (CUpdateObject slot): renders through 0x4E0A80 while +0x65 is set, through
 * 0x4E0750 while the node at +0x7C is null, otherwise does nothing (and returns EAX unchanged). */
/* @conv EAX,ECX 0 */
/* @func 004E0B80 custom */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_004E0A80(void *self);
DECOMP_C int __thiscall sub_004E0750(void *self);

DECOMP(004E0B80)
int __cdecl f_004E0B80(undefined4 in_eax, char *this)
{
    if (this[0x65])
        return sub_004E0A80(this);
    if (!*(void **)(this + 0x7c))
        return sub_004E0750(this);
    return in_eax;
}
