/* 0x004FDBD0: std::uninitialized_fill_n of the containers' allocator (in ECX, an empty class passed on as is): n copies
 * of *val from dst (0x0058CDD0, with the scalar/nonscalar tag of a byte), returns dst + n elements of 4 bytes */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_0058CDD0(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);

DECOMP(004FDBD0)
void * __thiscall f_004FDBD0(unsigned int alloc, void *dst, int n, void *val)
{
    sub_0058CDD0(val, dst, n, val, alloc, val, alloc & 0xffffff00);
    return (char *)dst + n * 4;
}
