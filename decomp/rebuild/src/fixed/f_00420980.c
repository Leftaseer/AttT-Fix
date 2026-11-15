/* 0x00420980: one step of a 2D scene: the base step at 0x004B1B20(this, arg), then a local 0x224-byte checkers
 * object (constructor 0x0043A280, destructor 0x0043A310) is filled with two passes over this->+0x7C (0x00430350 and
 * 0x00430430) around the arg's virtual slot +0x18, 0x0043A320, and finally this->+0x74 is handed to the setter at
 * 0x004AD530. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004B1B20(void *self, void *arg);
DECOMP_C void __thiscall sub_0043A280(void *self);
DECOMP_C void __thiscall sub_00430350(void *self);
DECOMP_C void __thiscall sub_0043A320(void *self);
DECOMP_C unsigned int __thiscall sub_00430430(void *self);
DECOMP_C void __thiscall sub_004AD530(void *value);
DECOMP_C void __thiscall sub_0043A310(void *self);

DECOMP(00420980)
void __thiscall f_00420980(void *self, void *arg)
{
    char *s = (char *)self;
    char checkers[0x224];
    sub_004B1B20(s, arg);
    sub_0043A280(checkers);
    sub_00430350(*(void **)(s + 0x7c));
    (*(void (__thiscall **)(void *))((char *)*(void **)arg + 0x18))(arg);
    sub_0043A320(checkers);
    sub_00430430(*(void **)(s + 0x7c));
    sub_004AD530(*(void **)(s + 0x74));
    sub_0043A310(checkers);
}
