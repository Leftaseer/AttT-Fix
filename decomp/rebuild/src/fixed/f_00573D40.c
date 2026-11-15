/* 0x00573D40: nSpell::Regeneration::vf34: a thunk for the regeneration's end step (0x00573AE0), which the original
 * calls with the spell passed by address; the callee's result (EAX) is returned. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_00573AE0(void *self, void *self_ref);

DECOMP(00573D40)
unsigned int __thiscall f_00573D40(void *this)
{
    return sub_00573AE0(this, &this);
}
