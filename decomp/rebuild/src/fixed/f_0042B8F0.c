/* 0x0042B8F0: scalar deleting destructor thunk for the subobject at +0x74 (the CScene part): adjusts this and jumps
 * into 0x0042BAF0. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C void *__thiscall sub_0042BAF0(void *this, unsigned int freeing);

DECOMP(0042B8F0)
void *__thiscall f_0042B8F0(char *this, unsigned int freeing)
{
    return sub_0042BAF0(this - 0x74, freeing);
}
