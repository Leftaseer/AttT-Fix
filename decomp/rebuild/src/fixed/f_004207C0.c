/* 0x004207C0: constructs the object: the base constructor at 0x004DF7D0, then the vtable at +0 (0x00607B30), then a
 * texture from 0x00443D00(arg) handed to 0x004DF020(this, texture, 1); the texture's fields at +0x1C and +0x20 are
 * copied to +0x54 and +0x58.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607B30[]; /* vftable */
DECOMP_C void __thiscall sub_004DF7D0(void *self);
DECOMP_C void *__cdecl sub_00443D00(void *arg);
DECOMP_C void __thiscall sub_004DF020(void *self, void *texture, int flag);

DECOMP(004207C0)
void *__thiscall f_004207C0(void *self, void *arg)
{
    char *s = (char *)self;
    void *texture;
    sub_004DF7D0(s);
    *(const void **)s = d_00607B30;
    texture = sub_00443D00(arg);
    sub_004DF020(s, texture, 1);
    *(int *)(s + 0x54) = *(int *)((char *)texture + 0x1c);
    *(int *)(s + 0x58) = *(int *)((char *)texture + 0x20);
    return s;
}
