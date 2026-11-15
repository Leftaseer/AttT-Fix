/* 0x004251D0: C3DControlsManager::~C3DControlsManager: stores its vtable, then empties the ring whose sentinel
 * sits at +0x40 (the sentinel links to itself, the count at +0x44 drops to zero and every node is freed with the
 * MSVCR80 operator delete), frees the array at +0x58 after storing the vtable 0x00607D0C at +0x54, releases the
 * structure at +0x3C (0x0044CFE0) and finishes with the CUpdateObject base destructor (0x00424E00). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00607D88[];
DECOMP_C char d_00607D0C[];
DECOMP_C void __cdecl sub_005E3E9C(void *block); /* operator delete */
DECOMP_C void __cdecl sub_005E3EBA(void *block); /* operator delete[] */
DECOMP_C void __thiscall sub_0044CFE0(void *self);
DECOMP_C void __thiscall sub_00424E00(void *self);

DECOMP(004251D0)
void __thiscall f_004251D0(void *this)
{
    char *s = (char *)this;
    void **sentinel, **node;
    *(const void **)s = d_00607D88;
    sentinel = *(void ***)(s + 0x40);
    node = (void **)*sentinel;
    *sentinel = sentinel;
    sentinel[1] = sentinel;
    *(unsigned int *)(s + 0x44) = 0;
    while (node != sentinel) {
        void **next = (void **)*node;
        sub_005E3E9C(node);
        node = next;
    }
    *(const void **)(s + 0x54) = d_00607D0C;
    if (*(void **)(s + 0x58)) {
        sub_005E3EBA(*(void **)(s + 0x58));
        *(void **)(s + 0x58) = 0;
    }
    sub_0044CFE0(s + 0x3c);
    sub_00424E00(s);
}
