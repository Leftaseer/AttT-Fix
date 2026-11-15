/* 0x00427C00: a new map node of 0x34 bytes: left, parent and right (+0/+4/+8) cleared, the header flag +0x30 set
 * to 1 and the nil byte +0x31 cleared.  Returns the node (operator new's null result is not really checked). */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */

DECOMP(00427C00)
char *__cdecl f_00427C00(void)
{
    char *node = (char *)sub_005E3EAE(0x34);
    *(void **)node = 0;
    *(void **)(node + 4) = 0;
    *(void **)(node + 8) = 0;
    node[0x30] = 1;
    node[0x31] = 0;
    return node;
}
