/* 0x00428D40: allocates a 0x34-byte sound map node and builds it with 0x00428970 (the three links/keys, the
 * record and the red colour 0); a failed allocation is returned as null. */
/* @conv - 20 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);                  /* operator new */
DECOMP_C void *__thiscall sub_00428970(void *self, unsigned int a, unsigned int b, unsigned int c, char *rec,
                                       unsigned char flag);

DECOMP(00428D40)
void *__stdcall f_00428D40(unsigned int a, unsigned int b, unsigned int c, char *rec, unsigned char flag)
{
    void *node = sub_005E3EAE(0x34);
    if (node)
        sub_00428970(node, a, b, c, rec, flag);
    return node;
}
