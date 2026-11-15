/* 0x00427DD0: looks the key up in the map at +4: the descent keeps the least node not below the key, and that node is
 * written to *out (and out returned) only when its key is equal; otherwise the head marks "not found". */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00427DD0)
void *__thiscall f_00427DD0(void *this, void **out, unsigned int *key)
{
    char *head = *(char **)((char *)this + 4);
    char *node = head;
    char *p = *(char **)(head + 4);
    unsigned int k = *key;

    if (!p[0x31]) {
        do {
            if (*(unsigned int *)(p + 0xc) < k) {
                p = *(char **)(p + 8);
            } else {
                node = p;
                p = *(char **)p;
            }
        } while (!p[0x31]);
    }
    if (node == head || *(unsigned int *)(node + 0xc) > k)
        node = head;
    *out = node;
    return out;
}
