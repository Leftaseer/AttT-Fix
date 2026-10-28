/* 0x00533CA0: CNpc::Render: when shown (+0x324, +0x274) and near enough (0x00463E20 of the position +0x64, the
 * camera's vfEC and +0x98: under 10) 0x004AC890, the model's (+0x260) vf28(+0x2E4) and vfC0(that level); a selected
 * talker (0x005334E0, +0x36D, not +0x325) gets its marker (0x004B8710 of 0x6CA9E4); otherwise EAX as it came */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
/* @func 00533CA0 custom */
DECOMP_C int __cdecl sub_00463E20(void *pos, void *cam, void *extra);
DECOMP_C void __thiscall sub_004AC890(void *self);
DECOMP_C unsigned int __thiscall sub_005334E0(void *self);
DECOMP_C unsigned int __thiscall sub_004B8710(void *self, void *npc);
DECOMP_C char d_006CA9E4[];
typedef void *(__thiscall *vfEC_533CA0)(void *self);
typedef void (__thiscall *vf1_533CA0)(void *self, unsigned int a);

DECOMP(00533CA0)
unsigned int __cdecl f_00533CA0(void *this, unsigned int eax)
{
    char *s = (char *)this;
    void **m;
    int v;
    if (!s[0x324] || !s[0x274])
        return eax;
    m = *(void ***)(s + 0x260);
    v = sub_00463E20(s + 0x64, ((vfEC_533CA0)(*(void ***)m)[0xec / 4])(m), s + 0x98);
    if (v >= 10)
        return v;
    sub_004AC890(this);
    m = *(void ***)(s + 0x260);
    ((vf1_533CA0)(*(void ***)m)[0x28 / 4])(m, *(unsigned int *)(s + 0x2e4));
    m = *(void ***)(s + 0x260);
    ((vf1_533CA0)(*(void ***)m)[0xc0 / 4])(m, v);
    eax = sub_005334E0(this);
    if ((char)eax && s[0x36d] && s[0x324] && !s[0x325])
        return sub_004B8710(*(void **)d_006CA9E4, this);
    return eax;
}
