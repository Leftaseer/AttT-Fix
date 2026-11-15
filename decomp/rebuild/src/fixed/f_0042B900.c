/* 0x0042B900: scalar deleting destructor thunk for the subobject at +4 (the CCollector part): adjusts this and jumps
 * into 0x0042BAF0. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C void *__thiscall sub_0042BAF0(void *this, unsigned int freeing);

DECOMP(0042B900)
void *__thiscall f_0042B900(char *this, unsigned int freeing)
{
    return sub_0042BAF0(this - 4, freeing);
}
