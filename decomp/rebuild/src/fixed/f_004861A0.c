/* COcclusionCulling::vf2 0x004861A0: stores the vector (3 floats) at 0x20, copied as dwords; EAX is left with
 * its z as the machine code leaves it */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(004861A0)
unsigned int __thiscall f_004861A0(void *this, const unsigned int *v)
{
    unsigned int *d = (unsigned int *)((char *)this + 0x20);
    d[0] = v[0];
    d[1] = v[1];
    d[2] = v[2];
    return v[2];
}
