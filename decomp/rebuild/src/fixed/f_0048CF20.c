/* 0x0048CF20: std::uninitialized_fill_n of the containers' allocator (in ECX, an empty class passed on as is): n copies
 * of *val from dst (0x00456050, with the scalar/nonscalar tag of a byte), returns dst + n elements of 0x20 bytes */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00456050(void *eax, void *dst, int n, void *val, unsigned int alloc, void *val2, unsigned int tag);

DECOMP(0048CF20)
void * __thiscall f_0048CF20(unsigned int alloc, void *dst, int n, void *val)
{
    sub_00456050(val, dst, n, val, alloc, val, alloc & 0xffffff00);
    return (char *)dst + n * 0x20;
}
