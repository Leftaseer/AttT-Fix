/* 0x00434660: std::uninitialized_fill_n of the containers' allocator (in ECX, an empty class passed on as is): n copies
 * of *val from dst (0x00434460, with the scalar/nonscalar tag of a byte), returns dst + n elements of 0x1c bytes */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00434460(void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);

DECOMP(00434660)
void * __thiscall f_00434660(unsigned int alloc, void *dst, int n, void *val)
{
    sub_00434460(dst, n, val, alloc, val, alloc & 0xffffff00);
    return (char *)dst + n * 0x1c;
}
