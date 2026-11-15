/* 0x00429330: std::map::insert(key arg 2) for the ambient sound tree held at +4.  The lower bound is searched
 * (+0x31 is the head's nil flag, keys are the dword at +0xC); an insertion before the found node walks one step
 * back (0x004276C0) and verifies the predecessor's key; equal keys return the existing node.  The new node goes
 * through 0x00428E00 (the colour flag arg 3 is 1 when the node was reached by a left descent).  Like the original,
 * the key argument's own slot holds the iterator.  arg 1 receives the pair: the iterator and a byte that is 1 when
 * a node was inserted. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00428E00(void *self, void *out, unsigned char leftish, char *pos, char *rec);
DECOMP_C void __thiscall sub_004276C0(void *slot);

#define NIL(n) (((char *)(n))[0x31])

DECOMP(00429330)
void __thiscall f_00429330(void *this, unsigned char *out, unsigned int *key)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 4);
    char **iterslot = (char **)((char *)__builtin_frame_address(0) + 0xc);  /* the key argument's own slot */
    char *pos = *(char **)(head + 4);
    char *where;
    unsigned char leftish = 1;

    if (!NIL(pos)) {
        char *x;
        do {
            x = pos;
            leftish = *key < *(unsigned int *)(pos + 0xc);
            pos = leftish ? *(char **)pos : *(char **)(pos + 8);
        } while (!NIL(pos));
        pos = x;
    }
    where = pos;
    *iterslot = where;
    if (leftish) {
        if (where == *(char **)head) {
            sub_00428E00(s, iterslot, 1, where, (char *)key);
            *(char **)out = *iterslot;
            out[4] = 1;
            return;
        }
        sub_004276C0(iterslot);
    }
    if (*(unsigned int *)(*iterslot + 0xc) < *key) {
        sub_00428E00(s, iterslot, leftish, where, (char *)key);
        *(char **)out = *iterslot;
        out[4] = 1;
        return;
    }
    *(char **)out = *iterslot;
    out[4] = 0;
}
