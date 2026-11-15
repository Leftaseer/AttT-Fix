/* 0x004275E0: the map lookup probe: starting below the head's +4, it follows +0 (for keys not less than the
 * search key) or +8 (for smaller keys); the dword at +0xC is the key compared unsigned.  Returns the node. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(004275E0)
void *__thiscall f_004275E0(void *this, unsigned int *key)
{
    char *s = (char *)this;
    char *node = *(char **)(s + 4), *last, *next;
    if (!(*(char **)(node + 4))[0x31]) {
        last = node;
        next = *(char **)(node + 4);
        do {
            node = next;
            if (*(unsigned int *)(node + 0xc) < *key) {
                next = *(char **)(node + 8);
                node = last;
            }
            else {
                next = *(char **)node;
            }
            last = node;
        } while (!next[0x31]);
    }
    return node;
}
