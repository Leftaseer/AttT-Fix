/* 0x00585210: constructs a render object, forwards four arguments through its base and virtual
 * setup methods, and finishes with 0x005850A0. */
/* @conv ECX 16 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00582350(void *self);
DECOMP_C void __cdecl sub_004AB870(void *self, unsigned int in_eax, void *value);
DECOMP_C void __thiscall sub_005850A0(void *self);
DECOMP_C char d_0061DBEC[], d_0061DBE0[];
typedef unsigned int (__thiscall *setup_585210)(void *self, void *value);

DECOMP(00585210)
void *__thiscall f_00585210(char *this, void *first, void *second, void *third, void *fourth)
{
    unsigned int eax;
    sub_00582350(this);
    *(void **)this = d_0061DBEC;
    *(void **)(this + 0x214) = d_0061DBE0;
    eax = ((setup_585210)*(void **)(d_0061DBEC + 0x28))(this, fourth);
    sub_004AB870(this, eax, third);
    ((setup_585210)(*(void ***)this)[0x6c / 4])(this, second);
    ((setup_585210)(*(void ***)this)[0x98 / 4])(this, first);
    sub_005850A0(this);
    return this;
}
