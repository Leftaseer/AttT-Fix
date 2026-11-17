/* 0x0047ABA0: enumerates scene passes and renders every 0x21c-byte child with the two values at +0x1d8/+0x1d0. */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef void (__thiscall *pass_count_47ABA0)(void *self, unsigned int *count, unsigned int unused);
typedef void (__thiscall *pass_index_47ABA0)(void *self, unsigned int index);
typedef void (__thiscall *pass_simple_47ABA0)(void *self);
DECOMP_C void __thiscall sub_0047A400(void *self, void *first, void *second);

DECOMP(0047ABA0)
void __thiscall f_0047ABA0(char *this, void *scene)
{
    unsigned int count = 0, pass, i, children;
    void **vtable = *(void ***)scene;
    ((pass_count_47ABA0)vtable[0x18 / 4])(scene, &count, 0);
    for (pass = 0; pass < count; pass++) {
        ((pass_index_47ABA0)vtable[0x20 / 4])(scene, pass);
        children = *(unsigned int *)(this + 0x1e0);
        for (i = 0; i < children; i++)
            sub_0047A400(*(void **)(this + 0x1e4) + i * 0x21c,
                         *(void **)(this + 0x1d8), *(void **)(this + 0x1d0));
        ((pass_simple_47ABA0)vtable[0x24 / 4])(scene);
    }
    ((pass_simple_47ABA0)vtable[0x1c / 4])(scene);
}
