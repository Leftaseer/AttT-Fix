/* 0x00429920: std::map::erase(first, last) for the ambient sound tree held at +4: the full range [begin, head)
 * takes the same clearing path as 0x004298F0 and leaves the head in arg 1; otherwise the nodes are erased one by
 * one (0x00429030) until arg 3 is reached and arg 1 receives that last iterator. */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004293F0(void *self, char *node);
DECOMP_C void __thiscall sub_00429030(void *self, char **out, char *pos);
DECOMP_C void __thiscall sub_00427720(void *slot);

DECOMP(00429920)
void __thiscall f_00429920(void *this, char **out, char *first, char *last)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 4);
    char **firstslot = (char **)((char *)__builtin_frame_address(0) + 0xc);  /* arg 2's own slot */
    char *cur = first, *next;

    if (first == *(char **)head && last == head) {
        sub_004293F0(s, *(char **)(head + 4));
        *(char **)(head + 4) = head;
        *(unsigned int *)(s + 8) = 0;
        *(char **)head = head;
        *(char **)(head + 8) = head;
        *out = *(char **)head;
        return;
    }
    while (cur != last) {
        next = cur;
        sub_00427720(&next);
        sub_00429030(s, firstslot, cur);
        cur = next;
    }
    *out = cur;
}
