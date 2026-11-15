/* 0x00569530: asks every element of the ring hanging off [8] (each element's object sits at element+8) to do
 * its work with the argument; always returns 0. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00533700(void *self, unsigned int edx_in, void *arg);

DECOMP(00569530)
int __thiscall f_00569530(char *this, void *arg)
{
    char *node;

    for (node = **(char ***)(this + 8); node != *(char **)(this + 8); node = *(char **)node)
        sub_00533700(*(void **)(node + 8), 0, arg);
    return 0;
}
