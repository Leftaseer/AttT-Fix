/* 0x00503170: scalar deleting destructor: the value in the object at +0x14 goes through 0x502E40 on the
 * sub-object at +0x10, then that object is freed and its pointers cleared; with bit 0 of the flags set the
 * sub-object itself is freed. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00502E40(void *self, unsigned int *result, unsigned int value, void *object);
DECOMP_C void __cdecl sub_005E3E9C(void *p);

DECOMP(00503170)
void *__thiscall f_00503170(char *this, unsigned int flags)
{
    void *object = *(void **)(this + 0x14);
    unsigned int result;

    sub_00502E40(this + 0x10, &result, *(unsigned int *)object, object);
    sub_005E3E9C(*(void **)(this + 0x14));
    *(void **)(this + 0x14) = 0;
    *(void **)(this + 0x18) = 0;
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
