/* 0x00503260: clears the list at p+0x10: erases [begin, end) via 0x00502E40 (whose result iterator lands in the
 * argument's own stack slot), frees the head node and zeroes the head and size */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00502E40(void *list, void *out, void *first, void *last);
DECOMP_C void __cdecl sub_005E3E9C(void *p);

DECOMP(00503260)
void __cdecl f_00503260(unsigned int p)
{
    unsigned int *pp = (unsigned int *)((char *)__builtin_frame_address(0) + 8);
    char *o = (char *)*pp;
    void *head = *(void **)(o + 0x14);
    sub_00502E40(o + 0x10, pp, *(void **)head, head);
    sub_005E3E9C(*(void **)(o + 0x14));
    *(unsigned int *)(o + 0x14) = 0;
    *(unsigned int *)(o + 0x18) = 0;
}
